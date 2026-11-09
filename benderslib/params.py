# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from dataclasses import dataclass, fields

from .consts import BendersConsts as CST


@dataclass
class BendersParams:
    """Parameters for BendersLib that can be manipulated by the users.

    A :class:`BendersParams` instance is passed to the Benders algorithm during its initialization.
    The users may initialize a :class:`BendersParams` instance with customized parameters
    and then pass it to the Benders algorithm.
    Parameters that are not specified will take their default values.

    Example
    ----------------

    .. code-block:: python

        # Initialize with customized parameters
        params = BendersParams(tol_abs=1e-5, time_limit=3600)

        # Or, using a dictionary
        # params = BendersParams(**{'tol_abs': 1e-5, 'time_limit': 3600})

        # Or, using default parameters
        # params = BendersParams()

        BD = ClassicalBenders(mp, sp, complicating_vars, params=params)
    """

    # Theta (estimator in master problem for subproblem's objective)

    theta_lb: float = 0.0
    """Lower bound for the estimator variable in the master problem.
    
       The default value of ``0.0`` is suitable for subproblems with non-negative objective values.
       For problems where the subproblem's objective value can be negative, you need to adjust this 
       parameter to ensure the Benders algorithm converges correctly. 
       
       Ideally, this value should be
       as large as possible while still being a valid lower bound for the subproblem's objective value,
       to provide a tighter approximation in the master problem and potentially improve convergence.
       For example, you can get a valid lower bound by solving the linear relaxation of the subproblem
       if it contains integer variables. In stochastic programming, you can solve the subproblem of 
       each scenario independently without fixing the complicating variables to get a valid lower bound.
    """

    # Numerical

    tol_binary: float = 1e-5
    """Absolute tolerance for accepting variable values as 0 or 1 in built-in binary cuts.

    Must be finite and satisfy ``0 <= tol_binary < 0.5``. Set to zero to require exact
    binary values. Values outside this tolerance raise
    :class:`~benderslib.errors.NonBinaryVariableValueError` during cut construction.
    This parameter does not change the backend solver's integrality tolerance.
    """

    tol_obj_diff: float = 1e-6
    """Tolerance for estimator values and subproblem objective values comparison.
    
    When generating optimality cuts, the cut is added only if ``sub_obj - theta > tol_obj_diff``, 
    to avoid numerical issues. It is set to be equal to ``tol_abs`` by default.
    """
    tol_cut_diff: float = 1e-8
    """Tolerance for cut coefficients and RHS comparison.
    
    When adding a cut, if all coefficients and right-hand side (RHS) differ from an existing cut 
    by no more than ``tol_cut_diff``, the new cut is considered duplicate and will not be added.
    """
    cut_normalize: bool = False
    """Whether to normalize the cut coefficients and right-hand side (RHS) when adding a cut.
    
    If ``True``, the cut coefficients and RHS are normalized to have an L2 norm of at 
    most :attr:`~BendersParams.cut_max_norm` before being added to the master problem.
    This can help improve numerical stability in the master problem solver, especially 
    when the :ref:`cut coefficients have large magnitudes <manual_numerical_large_cut_coefficients>`.
    If ``False``, the cut coefficients and RHS are not normalized, and are added to 
    the master problem as they are generated.
    """
    cut_max_norm: float = 1e5
    """The maximum allowed L2 norm for the cuts' coefficients when normalizing cuts.

    This parameter is used when :attr:`~BendersParams.cut_normalize` is ``True``.
    When normalizing a cut, if the L2 norm of the cut's coefficient vector exceeds this threshold,
    the coefficients and right-hand side (RHS) of the cut are scaled down to have an L2 norm equal 
    to this threshold; otherwise, the cut is not modified.
    """

    # Convergence

    tol_abs: float = 1e-6
    """Absolute tolerance for convergence, terminate when ``abs(UB - LB) <= tol_abs``."""
    tol_rel: float = 1e-4
    """Relative tolerance for convergence, terminate when ``abs(UB - LB) / abs(UB) <= tol_rel``."""
    time_limit: float = float('Inf')
    """Time limit for the Benders algorithm in seconds."""
    iter_limit: int = float('Inf')
    """Iteration limit for the Benders algorithm."""

    # L-shaped method

    multi_opti_cut: bool = False
    """**[L-shaped method]** Whether to add multiple optimality cuts per scenario in the L-shaped method.
    
    If ``True``, estimator variables are added to the master problem for each scenario, 
    and an optimality cut is added for each scenario in each iteration;
    If ``False``, only one estimator variable is added to the master problem,
    and an aggregated optimality cut is added.
    One need to trade-off between the size of the master problem and the 
    number of iterations when deciding whether to use multiple optimality cuts.
    """
    multi_feas_cut: bool = False
    """**[L-shaped method]** Whether to add multiple feasibility cuts per scenario in the L-shaped method.
    
    If ``True``, all extreme rays are used to generate multiple feasibility cuts;
    If ``False``, one feasibility cut is added when a infeasible subproblem is found,
    and the subsequent subproblems will not be solved.
    """
    parallel_sub: bool = False
    """**[L-shaped method]** Whether to solve subproblems in parallel in the L-shaped method.
    
    If ``True``, the subproblems in a :class:`~benderslib.SubProblems` instance are solved in parallel;
    If ``False``, the subproblems are solved sequentially.
    Note that parallelizing subproblems may lead to faster convergence in some problems, 
    but may not always be beneficial. You should consider the size of the problem, 
    the number of scenarios, and the available computational resources when deciding 
    whether to use parallelization.
    """
    parallel_threads: int = -1
    """**[L-shaped method]** Number of threads to use for parallel subproblem solving.
    
    This parameter is used when :attr:`~BendersParams.parallel_sub` is ``True``. 
    If set to a positive integer, it specifies the number of threads to use for 
    parallel subproblem solving. If set to ``-1``, BendersLib will determine 
    the number of threads to use based on the available CPU cores.
    """

    # Combinatorial Benders

    use_iis_cut: bool = False
    """**[Combinatorial Benders]** Whether to use IIS-based feasibility cuts.
    
    If ``True``, before generating feasibility cuts, the IIS of the infeasible subproblem is computed,
    and only the variables in the IIS are used to generate the feasibility cuts.
    If ``False``, all complicating variables are used to generate the feasibility cuts.
    
    IIS-based cuts require additional computational time to compute the IIS,
    but may lead to faster convergence in some problems.
    
    You should ensure that the solver used for the subproblem supports IIS computation, see :ref:`solver-table`.
    """

    # Branch-and-check method

    use_bnc: bool = False
    """**[Branch-and-check]** Whether to use the Branch-and-check (Branch-and-Benders-cut) method. 
    
    If ``True``, the Benders cut are added as lazy constraints during the branch-and-bound process of the master problem,
    instead of being added after solving the master problem to optimality.
    If ``False``, the classical implementation is used, where the master problem is solved 
    to optimality before adding Benders cuts.
    
    Setting ``use_bnc = True`` and calling :meth:`BendersSolver.solve()` 
    is equivalent to using :meth:`BendersSolver.bnc_solve()` directly.
    """
    bnc_frac_sol: bool = False
    """**[Branch-and-check]** Whether to use fractional solutions to generate Benders cuts in the Branch-and-check method.
    
    If ``True``, Benders cuts are generated from fractional solutions of the master problem.
    If ``False``, Benders cuts are generated only from integer feasible solutions of the master problem.
    If you implement callbacks with :attr:`~benderslib.BendersContext.where` being 
    :attr:`~benderslib.BendersConsts.NODE`, this parameter is required to be ``True``, 
    since the solutions at the nodes can be fractional. Otherwise no cuts will be generated at the nodes,
    and the callback implemented will not work.
    
    .. danger::
        
        This feature is experimentally supported only in
        :class:`~benderslib.solvers.Copt`, 
        :class:`~benderslib.solvers.Cplex`, and 
        :class:`~benderslib.solvers.Gurobi`.
    """

    # Logging

    log_freq_sec: float = 0.5
    """Frequency (in seconds) to log messages to the console/file."""
    log_freq_iter: int = 1
    """Frequency (in iterations) to log messages to the console/file."""
    log_level: str = 'INFO'
    """Logging level can be ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``. 
    See Python's `logging levels <https://docs.python.org/3/library/logging.html#logging-levels>`_ for details."""
    log_to_console: bool = True
    """Whether to print log messages to the console."""
    log_file: str = None
    """File path to save log messages. If ``None``, logs are not saved to a file."""

    def __repr__(self):
        # Only print non-default parameters
        non_default_params = []
        for field in fields(self):
            field_name = field.name
            current_value = getattr(self, field_name)
            default_value = field.default
            if current_value != default_value:
                n = field_name + ':'
                non_default_params.append(
                    f" - {n.ljust(CST.LOG_NAME_WIDTH)}{current_value} [Default: {default_value}]")

        if non_default_params:
            return "Benders Parameters (non-default):\n" + "\n".join(non_default_params)
        else:
            return 'Benders Parameters: \n - All default'
