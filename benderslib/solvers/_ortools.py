# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import copy

from ortools.sat.python import cp_model

from ..consts import BendersConsts as CST
from ._base import SolverCPBase
from ..errors import BendersNotImplementedError


class Ortools(SolverCPBase):
    """OR-Tools solver interface for BendersLib.

    This class provides an interface to the OR-Tools CP-SAT solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    .. warning::

        Constraint Programming (CP) solvers does not technically support dual or extreme rays like
        Mathematical Programming (MP) solvers. Therefore, dual-based Benders methods like
        :class:`~benderslib.ClassicalBenders` are not compatible with :class:`Ortools`.
        :class:`Ortools` is typically used with :class:`~benderslib.CombinatorialBenders` and
        :class:`~benderslib.LogicBasedBenders` for solving subproblems modeled as CP problems.

    Parameters
    ---------------
    model: ortools.sat.python.cp_model.CpModel
        An instance of OR-Tools' ``cp_model.CpModel``.
    vars_map: dict[str, object]
        A dictionary mapping **all** (not only complicating) variable names to OR-Tools variable objects.
        This is necessary because OR-Tools does not provide a direct way to access variables by name.
    cons_vars: dict[object, list[str]], optional
        A dictionary mapping boolean indicator variable object associated with each constraint
        to the list of decision variable names involved in that constraint.
        This parameter is required when computing conflicting variables in the IIS, using :meth:`compute_iis`.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(
            self,
            model: cp_model.CpModel,
            vars_map: dict,
            cons_vars: dict = None,
            solver_options: dict = None
    ) -> None:
        super().__init__(model)

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        # Private attributes
        self._solver = cp_model.CpSolver()
        self._original_model = model
        self._original_vars_map = vars_map
        self._vars_map = vars_map
        self._cons_vars = cons_vars
        if cons_vars:
            self._cons_vars = {self.model.get_or_make_boolean_index(b): vars for b, vars in cons_vars.items()}

        self._sense = CST.MIN
        self._all_vars = [v.name for v in self.model.Proto().variables]
        self._int_vars = []
        self._bin_vars = []
        # self._var_bounds = {}
        # self._rhs = []
        self._constr_num = len(self.model.Proto().constraints)

        self.__standardize()
        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()

    def __sense_to_minimize(self):
        if self.model.Proto().objective.scaling_factor == -1.0:
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __setup_model(self, solver_options: dict = None):
        if solver_options:
            for key, value in solver_options.items():
                setattr(self._solver.parameters, key, value)

    def __copy_model(self):
        # See https://github.com/google/or-tools/blob/stable/ortools/sat/docs/model.md#model-copy
        # for how to copy models in OR-Tools
        to_clone = [self._original_model, self._original_vars_map]
        self.model, self._vars_map = copy.deepcopy(to_clone)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        var_values = self._integer_fix_values(var_values)
        self.__copy_model()

        for var_name, value in var_values.items():
            var = self._vars_map[var_name]
            self.model.Add(var == value)

    def unfix_vars(self, vars: list[str]) -> None:
        self.__copy_model()

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        res = {var_name: self._solver.value(self._vars_map[var_name]) for var_name in vars_to_get}
        return res

    def get_obj(self) -> float:
        return self._solver.ObjectiveValue()

    def solve(self) -> None:
        status = self._solver.Solve(self.model)
        self._update_status('ORTOOLS', status.value)

    def compute_iis(self) -> set[str]:
        """Compute the Irreducible Infeasible Subsystem (IIS) of the model if it is infeasible.

        This method can be useful for :doc:`../tutorials/cbd` to identify a set of conflicting
        (binary) variables that causing subproblem infeasibility.
        This set of variables can be smaller than the full set of complicating variables,
        thus potentially leading to stronger :class:`~benderslib.NoGoodFC`.

        This method requires the ``cons_vars`` parameter to be provided during initialization.

        .. caution::

            - IIS is not guaranteed to be unique.
            - Here we use OR-Tools' ``SufficientAssumptionsForInfeasibility`` method, which
              `may not return a minimal (irreducible) infeasible subsystem <https://groups.google.com/g/or-tools-discuss/c/qlVv2uSq1uo>`__,
              but it is always sufficient to prove infeasibility.

        Returns
        ---------------
        list[str]
            A list of variable names involved in the IIS.

        Example
        ---------------
        .. code-block:: python

                iis_vars = solver.compute_iis()

        """
        assumptions_core = self._solver.SufficientAssumptionsForInfeasibility()

        var_set = set()
        for cons in assumptions_core:
            var_set.update(self._cons_vars[cons])

        return var_set
