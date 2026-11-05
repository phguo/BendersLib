# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from pathlib import Path

import pytest

from .test_model_base import BaseTestModel

try:
    import coptpy as cp
    from benderslib.solvers import Copt

    copt_available = True
except ImportError:
    copt_available = False


@pytest.mark.skipif(not copt_available, reason="COPT is not installed")
class TestCoptModels(BaseTestModel):
    @pytest.fixture
    def model_pair(self, model_name):
        env = cp.Envr()
        models = []
        try:
            for _ in range(2):
                model = env.createModel()
                models.append(model)
                model.setParam(cp.COPT.Param.Logging, 0)
                model.readLp(str(Path(__file__).with_name(f"{model_name}.lp")))
                model.setParam(cp.COPT.Param.TimeLimit, 30)
            yield tuple(models)
        finally:
            for model in models:
                model.clear()
            env.close()

    @pytest.fixture
    def solver_class(self):
        return Copt

    def solve_direct(self, model):
        model.solve()
        assert model.status == cp.COPT.OPTIMAL
        return model.objval

    def snapshot_model(self, model):
        variables = {
            var.name: (var.lb, var.ub, var.vtype != cp.COPT.CONTINUOUS, var.obj)
            for var in model.getVars()
        }
        constraints = []
        for cons in model.getConstrs():
            row = model.getRow(cons)
            coefficients = {
                row.getVar(i).name: row.getCoeff(i) for i in range(row.getSize())
            }
            constraints.append((cons.name, coefficients, cons.lb, cons.ub))
        return variables, constraints, model.getAttr(cp.COPT.Attr.ObjConst)
