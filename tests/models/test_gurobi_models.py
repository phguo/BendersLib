# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from pathlib import Path

import pytest

from .test_model_base import BaseTestModel

try:
    import gurobipy as gp
    from benderslib.solvers import Gurobi

    gurobi_available = True
except ImportError:
    gurobi_available = False


@pytest.mark.skipif(not gurobi_available, reason="Gurobi is not installed")
class TestGurobiModels(BaseTestModel):
    @pytest.fixture
    def model_pair(self, model_name):
        models = []
        with gp.Env(params={"OutputFlag": 0}) as env:
            try:
                for _ in range(2):
                    model = gp.read(str(Path(__file__).with_name(f"{model_name}.lp")), env=env)
                    models.append(model)
                    model.Params.TimeLimit = 30
                yield tuple(models)
            finally:
                for model in models:
                    model.dispose()

    @pytest.fixture
    def solver_class(self):
        return Gurobi

    def solve_direct(self, model):
        model.optimize()
        assert model.Status == gp.GRB.OPTIMAL
        return model.ObjVal

    def snapshot_model(self, model):
        variables = {
            var.VarName: (var.LB, var.UB, var.VType != gp.GRB.CONTINUOUS, var.Obj)
            for var in model.getVars()
        }
        constraints = []
        for cons in model.getConstrs():
            row = model.getRow(cons)
            coefficients = {
                row.getVar(i).VarName: row.getCoeff(i) for i in range(row.size())
            }
            lhs = cons.RHS if cons.Sense in {">", "="} else -float("inf")
            rhs = cons.RHS if cons.Sense in {"<", "="} else float("inf")
            constraints.append((cons.ConstrName, coefficients, lhs, rhs))
        return variables, constraints, model.ObjCon
