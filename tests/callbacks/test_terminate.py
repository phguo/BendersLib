# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import unittest
from benderslib import ClassicalBenders, CST
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB


def make_master_problem():
    model = Model("Master")
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    z = model.addVar(name="z")
    model.setObjective(x)
    model.update()
    return model, [x.VarName, z.VarName]


def make_sub_problem():
    model = Model("Sub")
    master_x = model.addVar(name="x")
    y = model.addVar(name="y")
    master_z = model.addVar(name="z")
    model.setObjective(2 * y)
    model.addConstr(master_x + y + master_z == 14)
    model.addConstr(master_x - y == 2)
    model.update()
    return model


def make_infeasible_sub_problem():
    model = Model("Sub")
    master_x = model.addVar(name="x")
    y = model.addVar(name="y")
    master_z = model.addVar(name="z")
    model.setObjective(2 * y)
    model.addConstr(master_x + y + master_z >= 14)
    model.addConstr(master_x - y <= 2)
    # Makes it infeasible with master solution
    model.addConstr(master_x >= 15)
    model.update()
    return model


class TestCallbackTermination(unittest.TestCase):
    def setUp(self):
        self.master_model, self.complicating_vars = make_master_problem()
        self.sub_model = make_sub_problem()
        self.infeasible_sub_model = make_infeasible_sub_problem()

    def _run_test_with_callback(self, callback, sub_model=None):
        sub = sub_model if sub_model else self.sub_model
        benders = ClassicalBenders.from_models(
            self.master_model, Gurobi,
            sub, Gurobi,
            complicating_vars=self.complicating_vars
        )
        benders.params.log_to_console = False
        benders.register(callback)
        benders.solve()
        assert benders.result.status in [
            CST.TERMINATED,
            # Can converge before adding optimality/feasibility cuts
            CST.INFEASIBLE,
            CST.OPTIMAL
        ]

    def test_on_benders_start(self):
        def on_benders_start(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_benders_start)

    def test_on_iteration_start(self):
        def on_iteration_start(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_iteration_start)

    def test_on_master_build(self):
        def on_master_build(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_master_build)

    def test_on_sub_build(self):
        def on_sub_build(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_sub_build)

    def test_on_before_master_solve(self):
        def on_before_master_solve(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_before_master_solve)

    def test_on_after_master_solve(self):
        def on_after_master_solve(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_after_master_solve)

    def test_on_before_sub_solve(self):
        def on_before_sub_solve(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_before_sub_solve)

    def test_on_after_sub_solve(self):
        def on_after_sub_solve(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_after_sub_solve)

    def test_on_opti_cut_generated(self):
        def on_opti_cut_generated(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_opti_cut_generated)

    def test_on_feas_cut_generated(self):
        def on_feas_cut_generated(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_feas_cut_generated, sub_model=self.infeasible_sub_model)

    def test_on_opti_cut_added(self):
        def on_opti_cut_added(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_opti_cut_added)

    def test_on_feas_cut_added(self):
        def on_feas_cut_added(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_feas_cut_added, sub_model=self.infeasible_sub_model)

    def test_on_new_lower_bound(self):
        def on_new_lower_bound(context):
            if context.state.n_iter > 0:
                return CST.TERMINATE

        self._run_test_with_callback(on_new_lower_bound)

    def test_on_new_upper_bound(self):
        def on_new_upper_bound(context):
            if context.state.n_iter > 0:
                return CST.TERMINATE

        self._run_test_with_callback(on_new_upper_bound)

    def test_on_iteration_end(self):
        def on_iteration_end(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_iteration_end)

    def test_on_benders_end(self):
        def on_benders_end(context):
            return CST.TERMINATE

        self._run_test_with_callback(on_benders_end)


if __name__ == "__main__":
    unittest.main()
