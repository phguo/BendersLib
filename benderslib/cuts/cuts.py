# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import numpy as np
from itertools import zip_longest

from ..consts import BendersConsts as CST
from ..core import OptimalityCut, FeasibilityCut
from ..errors import NonBinaryVariableValueError
from ..params import BendersParams
from ..utils import is_all_binary


class ClassicalOC(OptimalityCut):
    """The optimality cut for :doc:`../tutorials/classical`.

    The cut uses the optimal dual solution to form a valid lower bound on the subproblem's cost,
    represented by the variable :math:`\\eta` in the master problem.

    .. math::
        \\eta \\geq \\bar{\\pi}^T (b - A x)

    In this cut, :math:`\\eta` is the variable representing the subproblem's cost, :math:`\\bar{\\pi}` is the optimal solution
    to the dual subproblem (dual values of primal constraints), :math:`A` and :math:`b` are the matrices that define
    the subproblem constraints, and :math:`x` are the complicating variables.
    This cut can be interpreted as a first-order Taylor approximation or a supporting hyperplane for the value
    function of the subproblem.

    Parameters
    ----------
    vars : list[str]
        A list of complicating variable names.
    var_coefs : dict
        A dictionary mapping complicating variable names to their coefficients in the subproblem constraints.
    dual_values : list
        A list of dual variable values obtained from solving the subproblem.
    rhs : list
        A list of right-hand side values of the subproblem constraints.
    estimator : str, optional
        The name of the master problem variable representing the subproblem's cost.

    Example
    ----------

    .. code-block:: python

        from benderslib import ClassicalOC

        # Assuming we have the following data from the subproblem
        vars = ['x1', 'x2']         # Complicating variables
        var_coefs = {
            'x1': [2, 3],           # Coefficients of x1 in subproblem constraints
            'x2': [1, 4],           # Coefficients of x2 in subproblem constraints
        }
        dual_values = [0.5, 1.0]    # Optimal dual values from the subproblem
        rhs = [10, 20]              # Right-hand side values of the subproblem constraints

        # Create the optimality cut
        cut = ClassicalOC(vars, var_coefs, dual_values, rhs)
    """

    def __init__(self, vars: list[str], var_coefs: dict, dual_values: list, rhs: list, estimator=CST.ESTIMATOR_NAME):
        coefs = [sum(a * b for a, b in zip_longest(dual_values, var_coefs)) for var, var_coefs in var_coefs.items()]
        cut_rhs = sum(a * b for a, b in zip_longest(dual_values, rhs))

        super().__init__(vars=vars + [estimator], coefs=coefs + [1.0], rhs=cut_rhs, sense='>=', name="ClassicalOC")


class ClassicalFC(FeasibilityCut):
    """The feasibility cut for :doc:`../tutorials/classical`.

    The cut is derived from an extreme ray of the subproblem, which acts as a certificate of infeasibility.
    It is defined as follows to cut off the region of master solutions that leads to this infeasibility.

    .. math::
        0 \\geq \\bar{r}^T (b - A x)

    where :math:`\\bar{r}` is an extreme ray of the dual subproblem, :math:`A` and :math:`b` are the matrices
    that define the subproblem constraints, and :math:`x` are the complicating variables.
    This cut is a direct application of Farkas' Lemma. The extreme ray :math:`\\bar{r}` is typically
    provided by the LP solver when it determines the primal subproblem is infeasible
    (and thus the dual is unbounded). It informs the master problem that any future choice of :math:`x`
    violating this constraint will also result in an infeasible subproblem.

    Parameters
    ----------
    vars : list[str]
        A list of complicating variable names.
    var_coefs : dict
        A dictionary mapping complicating variable names to their coefficients in the subproblem constraints.
    extreme_ray : list
        A list representing an extreme ray of the subproblem's feasible region.
    rhs : list
        A list of right-hand side values of the subproblem constraints.

    Example
    ----------

    .. code-block:: python

        from benderslib import ClassicalFC

        # Assuming we have the following data from the subproblem
        vars = ['x1', 'x2']         # Complicating variables
        var_coefs = {
            'x1': [2, 3],           # Coefficients of x1 in subproblem constraints
            'x2': [1, 4],           # Coefficients of x2 in subproblem constraints
        }
        extreme_ray = [1.0, 0.5]    # Extreme ray from the dual subproblem
        rhs = [10, 20]              # Right-hand side values of the subproblem constraints

        # Create the feasibility cut
        cut = ClassicalFC(vars, var_coefs, extreme_ray, rhs)
    """

    def __init__(self, vars: list[str], var_coefs: dict, extreme_ray: list, rhs: list):
        extreme_ray = [-r for r in extreme_ray]
        coefs = [sum(a * b for a, b in zip_longest(extreme_ray, var_coefs)) for var, var_coefs in var_coefs.items()]
        cut_rhs = sum(a * b for a, b in zip_longest(extreme_ray, rhs))

        # # Even slower when data is small
        # extreme_ray_v = -np.array(extreme_ray)
        # rhs_v = np.array(rhs)
        # coefs_m = np.array(list(var_coefs.values()))
        # coefs = list(coefs_m @ extreme_ray_v)
        # cut_rhs = float(extreme_ray_v @ rhs_v)

        super().__init__(vars=vars, coefs=coefs, rhs=cut_rhs, sense='>=', name="ClassicalFC")


class NoGoodFC(FeasibilityCut):
    """The feasibility cut for :doc:`../tutorials/cbd`.

    It is defined as follows to ensure at least one binary variable changes its value in the next iteration,

    .. math::
        \\sum_{i \\in I_1} (1 - x_i) + \\sum_{i \\in I_0} x_i \\geq 1

    where :math:`I_1` is the set of indices of binary variables that are 1 in the current solution,
    and :math:`I_0` is the set of indices of binary variables that are 0 in the current solution.
    It can be rewritten as follows.

    .. math::
        \\sum_{i \\in I_1} x_i - \\sum_{i \\in I_0} x_i \\leq |I_1| - 1

    These two forms can both be found in the literature.
    To make sure the cut is strong, :math:`|I_1 \\cup I_0|` should be **as small as possible**,
    i.e., only including the binary variables that are relevant to the infeasibility of the subproblem,
    which is usually a small subset of all binary variables in the master problem.

    Parameters
    ----------
    bin_var_values : dict
        A dictionary mapping binary variable names to their values in the current master problem solution.
    tol_binary : float, optional, default=1e-5
        Absolute tolerance for accepting values as 0 or 1. Must be finite and in ``[0, 0.5)``.

    Raises
    ----------
    NonBinaryVariableValueError
        If a variable value is not within :attr:`~benderslib.BendersParams.tol_binary` of 0 or 1.

    Example
    ----------

    .. code-block:: python

        from benderslib import NoGoodFC

        # Assuming we have the following binary variable values from the master problem
        bin_var_values = {
            'x1': 1,  # Binary variable x1 is 1
            'x2': 0,  # Binary variable x2 is 0
            'x3': 1,  # Binary variable x3 is 1
        }

        # Create the no-good feasibility cut
        cut = NoGoodFC(bin_var_values)

    .. hint::

        ``bin_var_values`` should ideally be a small subset of all binary variables in the master problem,
        only including those that are relevant to the infeasibility of the subproblem.
    """

    def __init__(self, bin_var_values: dict, tol_binary: float = BendersParams.tol_binary):
        if not is_all_binary(list(bin_var_values.values()), tol_binary):
            raise NonBinaryVariableValueError(tol_binary=tol_binary)

        var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
        var_ones = [var for var, val in bin_var_values.items() if val > 0.5]

        vars = var_ones + var_zeros
        coefs = [1.0] * len(var_ones) + [-1.0] * len(var_zeros)
        rhs = len(var_ones) - 1

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='<=', name="NoGoodFC")


class CombinatorialOC(OptimalityCut):
    """The optimality cut for  :doc:`../tutorials/cbd`.

    It is defined as follows to lower bound the estimator :math:`\\theta` for subproblem in the master problem.

    .. math::

        \\theta \\geq z^* - M \\left( \\sum_{i \\in I_1} (1 - x_i) + \\sum_{i \\in I_0} x_i \\right)

    where :math:`z^*` is the objective value of the subproblem given the current master problem solution,
    :math:`I_1` is the set of indices of binary variables that are 1 in the current solution,
    and :math:`I_0` is the set of indices of binary variables that are 0 in the current solution,
    and :math:`M` is a large constant.
    It can be rewritten as follows.

    .. math::
        \\theta - M \\sum_{i \\in I_1} x_i + M \\sum_{i \\in I_0} x_i \\geq z^* - M |I_1|

    To ensure validity, :math:`M` should be larger than the maximum possible objective value of the subproblem.
    If it is not specified, BendersLib set :math:`M = z^* - L` in each iteration,
    where :math:`L = \\bar{\\theta}` is a known lower bound on :math:`\\theta`,
    retrieved from the master problem in the current iteration.
    The cut is rewritten as follows.

    .. math::
        \\frac{\\theta}{z^* - L} - \\sum_{i \\in I_1} x_i + \\sum_{i \\in I_0} x_i \\geq \\frac{z^*}{z^* - L} - |I_1|

    This form is used when :math:`z^* - L \\neq 0` to improve the numerical stability.

    Parameters
    ----------

    bin_var_values : dict
        A dictionary mapping binary variable names to their values in the current master problem solution.
    sub_obj : float
        The objective value of the subproblem given the current master problem solution.
    big_m : float, optional, default=sub_obj
        A large constant used in the cut formulation.
    estimator : str, optional
        The name of the master problem variable representing the subproblem's cost.
    tol_binary : float, optional, default=1e-5
        Absolute tolerance for accepting values as 0 or 1. Must be finite and in ``[0, 0.5)``.

    Raises
    ----------
    NonBinaryVariableValueError
        If a variable value is not within :attr:`~benderslib.BendersParams.tol_binary` of 0 or 1.

    Example
    ----------

    .. code-block:: python

        from benderslib import CombinatorialOC

        # Assuming we have the following binary variable values from the master problem
        bin_var_values = {
            'x1': 1,  # Binary variable x1 is 1
            'x2': 0,  # Binary variable x2 is 0
            'x3': 1,  # Binary variable x3 is 1
        }
        sub_obj = 50  # Objective value of the subproblem given the current master problem solution

        # Create the combinatorial optimality cut
        cut = CombinatorialOC(bin_var_values, sub_obj)
    """

    def __init__(
            self,
            bin_var_values: dict,
            sub_obj: float,
            big_m: float = None,
            estimator: str = CST.ESTIMATOR_NAME,
            tol_binary: float = BendersParams.tol_binary
    ):
        if not is_all_binary(list(bin_var_values.values()), tol_binary):
            raise NonBinaryVariableValueError(tol_binary=tol_binary)

        var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
        var_ones = [var for var, val in bin_var_values.items() if val > 0.5]
        big_m = sub_obj if big_m is None else big_m

        if big_m == 0:
            # Form 1
            vars = [estimator] + var_ones + var_zeros
            coefs = [1.0] + [-big_m] * len(var_ones) + [big_m] * len(var_zeros)
            rhs = sub_obj - big_m * len(var_ones)
        else:
            # Form 2: same number of cuts, but faster to solve the master problem
            vars = [estimator] + var_ones + var_zeros
            coefs = [1.0 / big_m] + [-1.0] * len(var_ones) + [1.0] * len(var_zeros)
            rhs = sub_obj / big_m - len(var_ones)

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='>=', name="CombinatorialCut")


class LShapedOC(OptimalityCut):
    """The optimality cut for :doc:`../tutorials/lshaped` (single-cut & linear recourse).

    This class encapsulates the aggregation logic. It takes raw data from all
    scenarios (probabilities, duals, matrices) and computes the final cut.
    The cut represents the following inequality.

    .. math::
        \\theta \\geq \\sum_{\\omega} p_\\omega [\\pi_\\omega^T (h_\\omega - T_\\omega x)]

    Parameters
    ----------
    vars : list[str]
        A list of variable names for the complicating variables :math:`x`.
    probs : list[float]
        A list of probabilities for each scenario :math:`p_\\omega`.
    duals : list[list[float]]
        A list of lists, where each inner list contains the dual variable values :math:`\\pi_\\omega^T` for a scenario.
    rhss : list[list[float]]
        A list of lists, where each inner list is the right-hand side :math:`h_ω` for a scenario.
    var_coefs_list : list[dict]
        A list of dictionaries. Each dictionary maps variable names to their
        coefficient lists :math:`T_ω` for a scenario.
    estimator : str, optional
        The name of the master problem variable representing the subproblem's cost.

    Example
    ----------

    .. code-block:: python

        from benderslib import LShapedOC

        # Assuming we have the following data from multiple scenarios
        vars = ['x1', 'x2']     # Complicating variables
        probs = [0.5, 0.5]      # Probabilities for each scenario
        duals = [               # Dual variable values for each scenario
            [0.5, 1.0],         # Scenario 1 duals
            [0.3, 0.7]          # Scenario 2 duals
        ]
        rhss = [                # Right-hand side (RHS) values for each scenario
            [10, 20],           # Scenario 1 RHS
            [15, 25]            # Scenario 2 RHS
        ]
        var_coefs_list = [      # Coefficient lists for each scenario
            {                   # Scenario 1 coefficients
                'x1': [2, 3],
                'x2': [1, 4]
            },
            {                   # Scenario 2 coefficients
                'x1': [3, 2],
                'x2': [4, 1]
            }
        ]

        # Create the L-shaped optimality cut
        cut = LShapedOC(vars, probs, duals, rhss, var_coefs_list)
    """

    def __init__(
            self,
            vars: list[str],
            probs: list[float],
            duals: list[list[float]],
            rhss: list[list[float]],
            var_coefs_list: list[dict],
            estimator=CST.ESTIMATOR_NAME
    ):
        # Vectorized implementation
        probs_v = np.array(probs)
        duals_m = np.array(duals)
        rhss_m = np.array(rhss)

        # aggregated_rhs
        scenario_rhss = np.sum(duals_m * rhss_m, axis=1)
        aggregated_rhs = float(probs_v @ scenario_rhss)

        # aggregated_x_coefs
        aggregated_x_coefs = np.zeros(len(vars))
        for i, var in enumerate(vars):
            # Create a matrix for var coefficients across all scenarios
            var_coefs_m = np.array([var_coefs_list[j][var] for j in range(len(probs))])
            # Calculate the dot product for each scenario
            scenario_coef_sums = np.sum(duals_m * var_coefs_m, axis=1)
            # Aggregate the weighted sum
            aggregated_x_coefs[i] = probs_v @ scenario_coef_sums

        final_aggregated_x_coefs = aggregated_x_coefs.tolist()
        final_vars = vars + [estimator]
        final_coefs = final_aggregated_x_coefs + [1.0]
        super().__init__(vars=final_vars, coefs=final_coefs, rhs=aggregated_rhs, sense='>=', name="LShapedOC")


class GeneralizedOC(OptimalityCut):
    """The optimality cut for :doc:`../tutorials/gbd`.

    This cut uses the Lagrange multipliers from the subproblem to form a valid lower bound
    on the subproblem's cost, represented by the variable :math:`\\eta` in the master problem.
    It is assumed that the original problem is linearly separable into master and subproblem components,
    and the constraints of the master problem are linear.
    These assumptions are necessary for **linear** generalized optimality cuts.

    .. math::
        \\eta \\geq f_y(\\bar{y}) - \\bar{\\lambda}^T A (x - \\bar{x})

    In this cut,
    :math:`\\eta` is the variable representing the subproblem's cost.
    :math:`f_y(\\bar{y})` is the objective value of the subproblem given the current master problem solution :math:`\\bar{x}`.
    :math:`\\bar{\\lambda}` are the Lagrange multipliers (dual variable values) obtained from solving the subproblem.
    :math:`A` represents the coefficients of complicating variables in the subproblem constraints,
    and :math:`x` are the complicating variables.

    Parameters
    ----------

    vars : list[str]
        A list of complicating variable names.
    var_values : dict[str, float]
        A dictionary mapping variable names to their current values in the master problem.
    var_coefs : dict[str, list[float]]
        A dictionary mapping complicating variable names to their coefficients in the subproblem constraints.
    sub_obj : float
        The objective value of the subproblem given the current master problem solution.
    multipliers : list[float]
        A list of Lagrange multipliers (dual variable values) obtained from solving the subproblem.
    estimator : str, optional
        The name of the master problem variable representing the subproblem's cost.

    Example
    ----------

    .. code-block:: python

        from benderslib import GeneralizedOC

        # Assuming we have the following data from the subproblem
        vars = ['x1', 'x2']         # Complicating variables
        var_values = {              # Current values of complicating variables in the master problem
            'x1': 5,
            'x2': 10
        }
        var_coefs = {               # Coefficients of complicating variables in subproblem constraints
            'x1': [2, 3],           # Coefficients of x1 in subproblem constraints
            'x2': [1, 4],           # Coefficients of x2 in subproblem constraints
        }
        sub_obj = 100               # Objective value of the subproblem given the current master problem solution
        multipliers = [0.5, 1.0]    # Lagrange multipliers from the subproblem

        # Create the generalized optimality cut
        cut = GeneralizedOC(vars, var_values, var_coefs, sub_obj, multipliers)
    """

    def __init__(
            self,
            vars: list[str],
            var_values: dict[str, float],
            var_coefs: dict[str, list[float]],
            sub_obj: float,
            multipliers: list[float],
            estimator=CST.ESTIMATOR_NAME
    ):
        coefs = [sum(a * b for a, b in zip_longest(multipliers, var_coefs)) for var, var_coefs in var_coefs.items()]
        cut_rhs = sum(a * var_values[var] for a, var in zip_longest(coefs, var_coefs.keys())) + sub_obj

        super().__init__(vars=vars + [estimator], coefs=coefs + [1.0], rhs=cut_rhs, sense=">=", name="GeneralizedOC")


class GeneralizedFC(ClassicalFC):
    """The feasibility cut for :doc:`../tutorials/gbd`.

    The cut is derived from an extreme ray of the subproblem, which acts as a certificate of infeasibility.
    It is defined as follows to cut off the region of master solutions that leads to this infeasibility.

    .. math::
        0 \\geq \\bar{r}^T (b - A x)

    where :math:`\\bar{r}` is an extreme ray of the dual subproblem, :math:`A` and :math:`b` are the matrices
    that define the subproblem constraints, and :math:`x` are the complicating variables.
    This cut is a direct application of Farkas' Lemma. The extreme ray :math:`\\bar{r}` is typically
    provided by the LP solver when it determines the primal subproblem is infeasible
    (and thus the dual is unbounded). It informs the master problem that any future choice of :math:`x`
    violating this constraint will also result in an infeasible subproblem.

    Parameters
    ----------
    vars : list[str]
        A list of complicating variable names.
    var_coefs : dict
        A dictionary mapping complicating variable names to their coefficients in the subproblem constraints.
    extreme_ray : list
        A list representing an extreme ray of the subproblem's feasible region.
    rhs : list
        A list of right-hand side values of the subproblem constraints.

    Example
    ----------

    .. code-block:: python

        from benderslib import GeneralizedFC

        # Assuming we have the following data from the subproblem
        vars = ['x1', 'x2']         # Complicating variables
        var_coefs = {
            'x1': [2, 3],           # Coefficients of x1 in subproblem constraints
            'x2': [1, 4],           # Coefficients of x2 in subproblem constraints
        }
        extreme_ray = [1.0, 0.5]    # Extreme ray from the dual subproblem
        rhs = [10, 20]              # Right-hand side values of the subproblem constraints

        # Create the feasibility cut
        cut = GeneralizedFC(vars, var_coefs, extreme_ray, rhs)
    """

    def __init__(self, vars: list[str], var_coefs: dict, extreme_ray: list, rhs: list):
        super().__init__(vars, var_coefs, extreme_ray, rhs)
        self.name = "GeneralizedFC"


class GeneLShapedOC(OptimalityCut):
    """The optimality cut for :doc:`../tutorials/lshaped` (single-cut & convex recourse).

    It extends the L-shaped method to handle convex subproblems, acting as a hybrid
    of :class:`GeneralizedOC` and :class:`LShapedOC`. While :class:`LShapedOC` aggregates cuts from
    multiple linear subproblems, this class applies the principles of :class:`GeneralizedOC`
    (for single convex problems) to a multi-scenario setting.

    It constructs a single, aggregated optimality cut by taking a probability-weighted average
    of the generalized cuts from each convex subproblem. This enables the :class:`GeneLShaped`
    method to solve problems with multiple independent convex subproblems (e.g., stochastic
    programs with convex recourse), extending the capability of the standard :class:`LShaped`
    method which is limited to linear subproblems.

    The aggregated cut is of the form

    .. math::

        \\theta \\geq \\sum_{\\omega \\in \\Omega} p_\\omega \\left( f_\\omega(\\bar{x}) + \\nabla f_\\omega(\\bar{x})^T (x - \\bar{x}) \\right)

    where
    :math:`\\theta` is the estimator variable for the total subproblem cost in the master problem.
    :math:`\\Omega` is the set of all scenarios.
    :math:`p_\\omega` is the probability of scenario :math:`\\omega`.
    :math:`f_\\omega(\\bar{x})` is the objective value of the subproblem for scenario :math:`\\omega`
    at the complicating variable values :math:`\\bar{x}`.
    :math:`\\nabla f_\\omega(\\bar{x})` is the gradient of the subproblem objective function with respect to :math:`x`,
    evaluated at :math:`\\bar{x}`.
    It is computed as :math:`-\\lambda_\\omega^T T_\\omega`, where :math:`\\lambda_\\omega` are
    the Lagrange multipliers (duals) and :math:`T_\\omega` are the coefficients of :math:`x` in the subproblem constraints.

    Parameters
    ----------

    vars : list[str]
        A list of complicating variable names (:math:`x`).
    probs : list[float]
        A list of probabilities (:math:`p_\\omega`) for each scenario.
    var_values : dict[str, float]
        A dictionary mapping complicating variable names to their current values (:math:`\\bar{x}`).
    var_coefs_list : list[dict[str, list[float]]]
        A list of dictionaries, where each dictionary contains the coefficients (:math:`T_\\omega`) of the complicating variables for a scenario.
    sub_obj_list : list[float]
        A list of subproblem objective values (:math:`f_\\omega(\\bar{x})`) for each scenario.
    multipliers_list : list[list[float]]
        A list of Lagrange multipliers (:math:`\\lambda_\\omega`) for each scenario's constraints.
    estimator : str, optional
        The name of the master problem variable representing the subproblem's cost (:math:`\\theta`).

    Example
    ----------

    .. code-block:: python

        from benderslib import GeneLShapedOC

        # Data from two convex subproblems (scenarios)
        complicating_vars = ['x1', 'x2']
        master_solution = {'x1': 10, 'x2': 5}
        probs = [0.4, 0.6]

        # Scenario 1 results
        sub_obj_1 = 150.0
        var_coefs_1 = {'x1': [2.0, 1.0], 'x2': [1.5, 3.0]}
        multipliers_1 = [10.0, 5.0]

        # Scenario 2 results
        sub_obj_2 = 200.0
        var_coefs_2 = {'x1': [2.2, 1.1], 'x2': [1.8, 3.3]}
        multipliers_2 = [8.0, 12.0]

        # Create the generalized L-shaped optimality cut
        cut = GeneLShapedOC(
            vars=complicating_vars,
            probs=probs,
            var_values=master_solution,
            var_coefs_list=[var_coefs_1, var_coefs_2],
            sub_obj_list=[sub_obj_1, sub_obj_2],
            multipliers_list=[multipliers_1, multipliers_2]
        )
    """

    def __init__(
            self,
            vars: list[str],
            probs: list[float],
            var_values: dict[str, float],
            var_coefs_list: list[dict[str, list[float]]],
            sub_obj_list: list[float],
            multipliers_list: list[list[float]],
            estimator=CST.ESTIMATOR_NAME
    ):
        aggregated_rhs = 0.0
        aggregated_x_coefs_dict = {var: 0.0 for var in vars}

        for i in range(len(probs)):
            prob = probs[i]
            sub_obj = sub_obj_list[i]
            multipliers = multipliers_list[i]
            var_coefs = var_coefs_list[i]

            # For a single scenario, the cut is: eta >= f(x_bar) + grad(f(x_bar))^T * (x - x_bar)
            # The gradient is grad(f(x_bar))^T = -lambda^T * T
            # The cut is: eta >= f(x_bar) - (lambda^T * T) * x + (lambda^T * T) * x_bar
            # Rewritten: eta + (lambda^T * T) * x >= f(x_bar) + (lambda^T * T) * x_bar

            # Calculate the coefficient for x variables: (lambda^T * T)
            scenario_x_coefs = [sum(m * c for m, c in zip_longest(multipliers, var_coefs[var])) for var in vars]

            # Calculate the constant part for this scenario's cut: f(x_bar) + (lambda^T * T) * x_bar
            scenario_rhs = sub_obj + sum(c * var_values[var] for c, var in zip_longest(scenario_x_coefs, vars))

            # Aggregate the right-hand side, weighted by probability
            aggregated_rhs += prob * scenario_rhs

            # Aggregate the x coefficients, weighted by probability
            for j, var in enumerate(vars):
                aggregated_x_coefs_dict[var] += prob * scenario_x_coefs[j]

        final_aggregated_x_coefs = [aggregated_x_coefs_dict[var] for var in vars]
        final_vars = vars + [estimator]
        final_coefs = final_aggregated_x_coefs + [1.0]

        super().__init__(vars=final_vars, coefs=final_coefs, rhs=aggregated_rhs, sense='>=', name="GeneLShapedOC")
