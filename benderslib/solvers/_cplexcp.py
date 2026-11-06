# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from ..consts import BendersConsts as CST
from ._base import SolverCPBase
from ..errors import BendersNotImplementedError

from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoSolveResult


class CplexCP(SolverCPBase):
    """CPLEX CP solver interface for BendersLib.

    This class provides an interface to the CPLEX CP solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    .. warning::

        Constraint Programming (CP) solvers does not technically support dual or extreme rays like
        Mathematical Programming (MP) solvers. Therefore, dual-based Benders methods like
        :class:`~benderslib.ClassicalBenders` are not compatible with :class:`CplexCP`.
        :class:`CplexCP` is typically used with :class:`~benderslib.CombinatorialBenders` and
        :class:`~benderslib.LogicBasedBenders` for solving subproblems modeled as CP problems.

    Parameters
    ---------------
    model: docplex.cp.model.CpoModel
        An instance of CPLEX's ``CpoModel``.
    vars_map: dict[str, object]
        A dictionary mapping **all** (not only complicating) variable names to CPLEX variable objects.
    cons_vars: dict[str, list[str]], optional
        A dictionary mapping CPLEX constraint name to the list of decision variable names involved in
        the corresponding constraints. This parameter is required when computing conflicting variables
        in the IIS, using :meth:`compute_iis`.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(
            self, model: CpoModel,
            vars_map: dict,
            cons_vars: dict = None,
            solver_options: dict = None
    ) -> None:
        super().__init__(model)

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        # Private attributes
        self._original_model = model
        self._vars_map = vars_map
        self._solver_options = solver_options or {}
        self._solution: CpoSolveResult | None = None
        self._is_sat = not self.model.is_minimization() and not self.model.is_maximization()
        self._cons_vars = cons_vars

        self._sense = CST.MIN
        self._all_vars = [v.name for v in self._vars_map.values()]
        self._constr_num = self.model.get_statistics().get_number_of_constraints()

        _options = self._options['CPLEXCP_OPTIONS']
        # Prioritize user options
        _options.update(self._solver_options)
        self._solver_options = _options

        self.__standardize()

    def __standardize(self):
        self.__sense_to_minimize()

    def __sense_to_minimize(self):
        if not self._is_sat and self.model.is_maximization():
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __copy_model(self):
        self.model = self._original_model.clone()

    def fix_vars(self, var_values: dict[str, float]) -> None:
        var_values = {name: round(value) for name, value in var_values.items()}
        self.__copy_model()

        for var_name, value in var_values.items():
            var = self._vars_map[var_name]
            self.model.add((var == value).set_name(f'__fix_{var_name}'))

            self._cons_vars[f'__fix_{var_name}'] = [var_name]

    def unfix_vars(self, vars: list[str]) -> None:
        self.__copy_model()

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        if not self._solution:
            return {}
        vars_to_get = vars or self._all_vars
        res = {var_name: self._solution.get_value(self._vars_map[var_name]) for var_name in vars_to_get}
        return res

    def get_obj(self) -> float:
        obj_val = self._solution.get_objective_value()
        if obj_val is None and self._is_sat:
            return 0.0
        return obj_val

    def solve(self) -> None:
        self._solution = self.model.solve(**self._solver_options)
        self._update_status('CPLEXCP', self._solution.get_solve_status().lower())

    def compute_iis(self) -> set[str]:
        """Compute the Irreducible Infeasible Subsystem (IIS) of the model if it is infeasible.

        This method can be useful for :doc:`../tutorials/cbd` to identify a set of conflicting
        (binary) variables that causing subproblem infeasibility.
        This set of variables can be smaller than the full set of complicating variables,
        thus potentially leading to stronger :class:`~benderslib.NoGoodFC`.

        This method requires the ``cons_vars`` parameter to be provided during initialization.

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

        # https://ibmdecisionoptimization.github.io/docplex-doc/cp/docplex.cp.model.py.html#docplex.cp.model.CpoModel.refine_conflict
        # https://ibmdecisionoptimization.github.io/docplex-doc/cp/docplex.cp.solution.py.html#docplex.cp.solution.CpoRefineConflictResult

        conflict = self.model.refine_conflict(**self._solver_options)

        var_set = set()

        # Variables
        for var in conflict.get_member_variables():
            var_name = var.get_name()
            var_set.add(var_name)

        # Constraints
        for cons in conflict.get_member_constraints():
            cons_name = cons.get_name()
            var_set.update(self._cons_vars[cons_name])

        return var_set
