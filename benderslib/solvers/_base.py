# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from abc import ABC, abstractmethod
from copy import deepcopy

from ..consts import BendersConsts as CST
from ..config import config as solver_config
from ..errors import BendersNotImplementedError


class SolverBase(ABC):
    """The abstract base class for solver interfaces in BendersLib.

    It defines the essential methods and attributes that any solver interface must implement
    to be compatible with BendersLib.

    Parameters
    ---------------
    model :
        An instance of the solver's model class (e.g., Gurobi's ``gurobipy.Model``).
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model, solver_options: dict = None) -> None:
        self.model = model
        """A copy of the original solver model instance.

                This attribute is exactly the solver-specific model instance passed during initialization.
                It allows direct access to solver-specific features (attributes and methods) not covered by the abstract interface.
                Refer to :ref:`solver-table` for supported solvers, and their documentation.
                """
        self.status = CST.UNSOLVED
        """The status of the last solve attempt.
        
        It is initialized to :const:`~benderslib.BendersConsts.UNSOLVED`,
        and it should be updated to :const:`~benderslib.BendersConsts.OPTIMAL` 
        or :const:`~benderslib.BendersConsts.INFEASIBLE`, 
        after calling the :func:`~benderslib.SolverBase.solve` method.

        .. caution::
            :attr:`status` should only be set to :const:`~benderslib.BendersConsts.OPTIMAL` 
            or :const:`~benderslib.BendersConsts.INFEASIBLE`,
            since it is not clear how other statuses (e.g., feasible but not optimal)
            would impact convergence of Benders decomposition.
        """

        self._options = deepcopy(solver_config)
        """A dictionary of solver-specific options loaded from the configuration file."""

        # Attributes to be set in the subclass
        # Below are for printing and reporting purposes
        self._sense = CST.MIN
        """An indicator of the objective sense of the model."""
        self._all_vars: list[str] = []
        """A list of all variable names in the model."""
        self._int_vars: list[str] = []
        """A list of all integer variable names in the model."""
        self._bin_vars: list[str] = []
        """A list of all binary variable names in the model."""
        self._var_bounds: dict[str, tuple[float, float]] = {}
        """A dictionary mapping variable names to their lower and upper bounds."""
        self._rhs: list[float] = []
        """A list of right-hand side values for all constraints in the model."""
        self._constr_num: int | None = None
        """The number of constraints in the model."""

    @abstractmethod
    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        """Add estimator variable(s) to the objective function of the model.

        Parameters
        ---------------
        estimators : list[str]
            A list of names for the estimator variables to be added.
        prob : list[float]
            A list of probabilities (weights) associated with each estimator variable.
            The length of ``prob`` should match that of ``estimators``.
            If ``None``, equal weights are assigned to all estimator variables.
            Note that the sum of probabilities does not need to equal 1.
        lb : float
            The lower bound for the estimator variables. Default is ``0.0``.

        Example
        ---------------
        .. code-block:: python

                # Adding multiple estimators with specified probabilities
                solver.add_estimators(
                    estimators=['theta1', 'theta2'],
                    prob=[0.3, 0.7],
                    lb=0.0
                )

                # Adding a single estimator
                solver.add_estimators(['theta'])
        """
        ...

    @abstractmethod
    def fix_vars(self, var_values: dict[str, float]) -> None:
        """Fix the values of specified variables in the model.

        Parameters
        ---------------
        var_values : dict[str, float]
            A dictionary mapping variable names to their fixed values.

        Example
        ---------------

        .. code-block:: python

                solver.fix_vars({'x1': 10, 'x2': 5.5})
        """
        ...

    @abstractmethod
    def unfix_vars(self, vars: list[str]) -> None:
        """Unfix the specified variables in the model by restoring their original bounds.

        Parameters
        ---------------
        vars : list[str]
            A list of variable names to be unfixed.

        Example
        ---------------

        .. code-block:: python

                solver.unfix_vars(['x1', 'x2'])
        """
        ...

    @abstractmethod
    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        """Get the current values of specified variables in the model.

        Parameters
        ---------------
        vars : list[str] or None
            A list of variable names to retrieve values for. If ``None``, retrieves values for all variables

        Returns
        ---------------
        dict[str, float]
            A dictionary mapping variable names to their current values.

        Example
        ---------------

        .. code-block:: python

                values = solver.get_var_values(['x1', 'x2'])
                # or get all variable values
                all_values = solver.get_var_values()

        """
        ...

    @abstractmethod
    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        """Get the coefficients of specified variables in all the constraints of the model.

        Parameters
        ---------------
        vars : list[str] or None
            A list of variable names to retrieve coefficients for. If ``None``, retrieves coefficients for all variables.

        Returns
        ---------------
        dict[str, list]
            A dictionary mapping variable names to a list of their coefficients in each constraint.

        Example
        ---------------
        .. code-block:: python

                coefs = solver.get_var_coefs(['x1', 'x2'])
                # or get coefficients for all variables
                all_coefs = solver.get_var_coefs()
        """
        ...

    @abstractmethod
    def get_rhs(self) -> list[float]:
        """Get the right-hand side values of all constraints in the model.

        Returns
        ---------------
        list[float]
            A list of right-hand side values for each constraint.

        Example
        ---------------
        .. code-block:: python

                rhs = solver.get_rhs()
        """
        ...

    @abstractmethod
    def get_dual_values(self) -> list[float]:
        """Get the dual values (shadow prices) of all constraints in the model.

        This is essential for generating :class:`Classical Benders optimality cuts <ClassicalOC>`.

        Returns
        ---------------
        list[float]
            A list of dual values for each constraint.

        Example
        ---------------
        .. code-block:: python

                pi = solver.get_dual_values()
        """
        ...

    @abstractmethod
    def get_extreme_ray(self) -> list[float]:
        """Get the extreme ray of the model.

        This is essential for generating :class:`Classical Benders feasibility cuts <ClassicalFC>`.

        Returns
        ---------------
        list[float]
            A list representing the extreme ray.

        Example
        ---------------
        .. code-block:: python

                ray = solver.get_extreme_ray()
        """
        ...

    @abstractmethod
    def get_obj(self) -> float:
        """Get the objective value of the model after solving.

        Returns
        ---------------
        float
            The objective value.

        Example
        ---------------
        .. code-block:: python

                obj_val = solver.get_obj()
        """
        ...

    @abstractmethod
    def add_cut(self, cut, name) -> None:
        """Add a Benders cut to the solver's model as a constraint.

        Parameters
        ---------------
        cut : :class:`~benderslib.Cut`
            An instance of a :class:`~benderslib.Cut`,
            either :class:`~benderslib.OptimalityCut` or :class:`~benderslib.FeasibilityCut`.
        name : str
            The name of the constraint to be added.

        Example
        ---------------
        .. code-block:: python

                from benderslib import OptimalityCut

                cut = OptimalityCut(vars=['x1', 'x2'], coefs=[1.0, 2.0], rhs=10.0, sense=CST.GEQ)
                solver.add_cut(cut, name='BendersOC_1')
        """
        ...

    @abstractmethod
    def remove_cut(self, cut_name: str) -> None:
        """Remove a constraint from the solver's model by its name.

        Parameters
        ---------------
        cut_name : str
            The name of the constraint to be removed.

        Example
        ---------------
        .. code-block:: python

                solver.remove_cut('BendersOC_1')
        """
        ...

    @abstractmethod
    def solve(self) -> None:
        """Solve the optimization model using the solver's built-in optimization method.

        Solver-specific parameters can be set in this method,
        such as hiding the solver's output log in the console.
        After solving, :attr:`status` should be updated accordingly
        to :const:`~benderslib.BendersConsts.OPTIMAL` or :const:`~benderslib.BendersConsts.INFEASIBLE`.

        .. caution::
            :attr:`status` should only be set to :const:`~benderslib.BendersConsts.OPTIMAL`
            or :const:`~benderslib.BendersConsts.INFEASIBLE`,
            since it is not clear how other statuses (e.g., feasible but not optimal)
            would impact convergence of Benders decomposition.
        """
        ...

    def _update_status(self, solver_name: str, raw_status: int | str) -> None:
        """Update the status attribute based on the backer solver's raw status code.

        Parameters
        ---------------
        solver_name:
            The name of the solver (e.g., 'GUROBI', 'CPLEX', 'PYOMO', etc.).
        raw_status:
            The raw status code returned by the solver after solving.
        """
        solver_status_map = self._options['STATUS_CODES'][solver_name.upper()]
        status_str = solver_status_map.get(raw_status, 'UNKNOWN')
        self.status = getattr(CST, status_str, CST.UNKNOWN)

    def compute_iis(self) -> set[str]:
        """Compute the Irreducible Infeasible Subsystem (IIS) of the model if it is infeasible.

        This method can be useful for :doc:`../tutorials/cbd` to identify a set of conflicting
        (binary) variables that causing subproblem infeasibility.
        This set of variables can be smaller than the full set of complicating variables,
        thus potentially leading to stronger :class:`~benderslib.NoGoodFC`.

        .. caution::

            IIS is not guaranteed to be unique.

        Returns
        ---------------
        list[str]
            A list of variable names involved in the IIS.

        Example
        ---------------
        .. code-block:: python

                iis_vars = solver.compute_iis()

        """
        ...

    @staticmethod
    def make_master_problem(original_model, master_vars: list[str]) -> object:
        """Build the master problem from the original problem.

        The master problem is built from a copy of the original problem, following these steps.

        1. In the variable set, remove all non-master variables.
        2. In the objective function, remove all terms involving non-master variables.
        3. In the constraints, remove constraints that contains non-master variables.

        .. admonition:: Master problem variables vs. complicating variables
            :class: note

            The **master problem variables** are variables that appears only in the master problem.
            It has a subset, **complicating variables**, which are variables that are passed to the subproblem
            as known parameters.
            Though they are *sometimes identical*, the decomposition is based on the former.

        Parameters
        ---------------
        original_model :
            An instance of a solver's model class (e.g., Gurobi's ``gurobipy.Model``).
        master_vars : list[str]
            A list of variable names that are considered master problem variables.

        Returns
        ---------------
        object
            A new model instance representing the master problem, in the solver-specific format.

        Example
        ---------------
        .. code-block:: python

                from benderslib.solvers import Gurobi

                original_model = ...
                # It is a static method, which can be called without initializing an instance
                master_model = Gurobi.make_master_problem(original_model, ['x1', 'x2'])
        """
        ...

    @staticmethod
    def make_sub_problem(original_model, master_vars: list[str]) -> object:
        """Build the subproblem from the original problem.

        The subproblem is built from a copy of the original problem, following these steps.

        1. In the variable set, make the master variables be continuous variables.
           They will be fixed later when solving the subproblem.
        2. In the objective function, remove all terms involving master variables.
        3. In the constraints, remove constraints that contains only master variables.

        .. admonition:: Master problem variables vs. complicating variables
            :class: note

            The **master problem variables** are variables that appears only in the master problem.
            It has a subset, **complicating variables**, which are variables that are passed to the subproblem
            as known parameters.
            Though they are *sometimes identical*, the decomposition is based on the former.

        Parameters
        ---------------
        original_model :
            An instance of a solver's model class (e.g., Gurobi's ``gurobipy.Model``).
        master_vars : list[str]
            A list of variable names that are considered master problem variables.

        Returns
        ---------------
        object
            A new model instance representing the subproblem, in the solver-specific format.

        Example
        ---------------
        .. code-block:: python

                from benderslib.solvers import Gurobi

                original_model = ...
                # It is a static method, which can be called without initializing an instance
                sub_model = Gurobi.make_sub_problem(original_model, ['x1', 'x2'])
        """
        ...


class SolverCPBase(SolverBase):
    """The abstract base class for Constraint Programming (CP) solver interfaces in BendersLib.

    It defines the essential methods and attributes that any CP solver interface must implement
    to be compatible with BendersLib.

    Parameters
    ---------------
    model :
        An instance of the solver's model class (e.g., Gurobi's ``gurobipy.Model``).
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model, solver_options: dict = None) -> None:
        super().__init__(model, solver_options)

    # Below are functions required when using this solver as a master problem solver.
    # Using CP solver for master problem is not common, so these functions are left unimplemented.

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.add_estimators.__name__)

    def add_cut(self, cut, name=None) -> None:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.add_cut.__name__)

    def remove_cut(self, cut_name: str) -> None:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.remove_cut.__name__)

    # Below are not technically available for a CP solver.

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.get_var_coefs.__name__)

    def get_rhs(self) -> list[float]:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.get_rhs.__name__)

    def get_dual_values(self) -> list[float]:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.get_dual_values.__name__)

    def get_extreme_ray(self) -> list[float]:
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func=self.get_extreme_ray.__name__)

    @staticmethod
    def make_master_problem(original_model, master_vars: list[str]):
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func="make_master_problem")

    @staticmethod
    def make_sub_problem(original_model, master_vars: list[str]):
        raise BendersNotImplementedError(  # pragma: no cover
            "Not support for a Constraint Programming solver.", func="make_sub_problem")
