# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from pathlib import Path

import pytest

from .test_model_base import BaseTestModel

try:
    from pyscipopt import Model
    from benderslib.solvers import Scip

    scip_available = True
except ImportError:
    scip_available = False


@pytest.mark.skipif(not scip_available, reason="SCIP is not installed")
class TestScipModels(BaseTestModel):
    @pytest.fixture
    def model_pair(self, model_name):
        models = []
        try:
            for _ in range(2):
                model = Model()
                models.append(model)
                model.hideOutput()
                model.readProblem(str(Path(__file__).with_name(f"{model_name}.lp")))
                model.setRealParam("limits/time", 30)
            yield tuple(models)
        finally:
            for model in models:
                model.freeProb()

    @pytest.fixture
    def solver_class(self):
        return Scip

    def solve_direct(self, model):
        model.optimize()
        assert model.getStatus() == "optimal"
        return model.getObjVal()

    def snapshot_model(self, model):
        variables = {
            var.name: (
                var.getLbOriginal(), var.getUbOriginal(),
                var.vtype() in {"BINARY", "INTEGER", "IMPLINT"}, var.getObj(),
            )
            for var in model.getVars(transformed=False)
        }
        constraints = [
            (cons.name, model.getValsLinear(cons), model.getLhs(cons), model.getRhs(cons))
            for cons in model.getConss(transformed=False)
        ]
        return variables, constraints, model.getObjoffset()
