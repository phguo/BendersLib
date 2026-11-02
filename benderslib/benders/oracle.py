# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""Oracle-based Logic-Based Benders Decomposition."""

import inspect
from typing import Callable, Type

from ..consts import BendersConsts as CST
from ..core import (
    BendersParams,
    BendersSolver,
    Cut,
    CutGenerator,
    LogicBasedSubProblem,
    MasterProblem,
    Oracle,
    _FuncWrapperOracle,
)


class _OracleSubProblem(LogicBasedSubProblem):
    """Adapts an oracle to the subproblem interface used by :class:`BendersSolver`."""

    def __init__(self, complicating_vars, oracle: Oracle, params: BendersParams):
        super().__init__(complicating_vars, params)
        self.oracle = oracle
        self.cuts: list[Cut] = []

    def solve(self):
        result = self.oracle.evaluate()

        if not isinstance(result, tuple) or len(result) != 3:
            raise ValueError("Oracle must return (cuts, sub_obj, var_values).")  # pragma: no cover

        cuts, sub_obj, var_values = result

        if not isinstance(cuts, list) or not all(isinstance(cut, Cut) for cut in cuts):
            raise ValueError("Oracle cuts must be a list of Cut instances.")  # pragma: no cover
        if sub_obj is not None and not isinstance(var_values, dict):
            raise ValueError("Oracle var_values must be a dict when sub_obj is provided.")  # pragma: no cover
        if not cuts and sub_obj is None:
            raise ValueError("Oracle must return cuts or a subproblem objective value.")  # pragma: no cover

        self.cuts = cuts
        self.obj = sub_obj
        self.var_values = var_values
        self.status = CST.OPTIMAL if sub_obj is not None else CST.INFEASIBLE


class _OracleCutGenerator(CutGenerator):
    """Returns the cuts produced by an oracle evaluation."""

    def generate(self):
        return self.sub_problem.cuts


class OracleBenders(BendersSolver):
    """An oracle-based implementation of :doc:`../tutorials/lbbd`.

    This is an additive alternative to :class:`LogicBasedBenders`. An oracle
    evaluates the current master solution and generates its cuts in one step.

    Parameters
    ----------
    master_problem : MasterProblem
        The master problem instance.
    oracle : Type[Oracle] | Callable
        An :class:`Oracle` subclass or a function with signature
        ``oracle(master_problem) -> (cuts, sub_obj, var_values)``.
    complicating_vars : list[str]
        Names of the complicating variables.
    params : BendersParams, optional
        The Benders parameters.

    Example
    -------

    .. code-block:: python

        from benderslib import Oracle, OracleBenders, MasterProblem
        from benderslib.solvers import Gurobi

        # Define master problem model
        master_model = ...  # Define your master problem model here
        mp = MasterProblem(Gurobi(master_model))

        # Define a custom oracle
        class MyOracle(Oracle):
            def evaluate(self):
                master_values = self.master_problem.get_var_values()
                sub_obj = 2 * master_values['x']
                var_values = {'y': master_values['x']}

                # Add any valid Cut instances required by your logic.
                cuts = []
                return cuts, sub_obj, var_values

        # Define complicating variables
        complicating_vars = ['x']

        # Initialize and solve
        BD = OracleBenders(mp, MyOracle, complicating_vars)
        BD.solve()
    """

    @classmethod
    def from_models(cls, *args, **kwargs):
        raise NotImplementedError("OracleBenders does not have a from_models method.")  # pragma: no cover

    def __init__(
            self,
            master_problem: MasterProblem,
            oracle: Type[Oracle] | Callable,
            complicating_vars: list[str],
            params: BendersParams | None = None,
    ):
        params = params if params is not None else BendersParams()
        oracle = self._initialize_oracle(oracle, master_problem, params)
        sub_problem = _OracleSubProblem(complicating_vars, oracle, params)

        super().__init__(
            master_problem,
            sub_problem,
            complicating_vars,
            _OracleCutGenerator,
            _OracleCutGenerator,
            params,
        )
        self.oracle = oracle
        """The oracle instance used to evaluate master solutions (see :class:`Oracle`)."""

    @staticmethod
    def _initialize_oracle(oracle, master_problem, params):
        if inspect.isfunction(oracle):
            return _FuncWrapperOracle(master_problem, oracle, params)
        if inspect.isclass(oracle) and issubclass(oracle, Oracle):
            return oracle(master_problem, params)
        raise TypeError("Oracle must be a function or an Oracle subclass.")  # pragma: no cover
