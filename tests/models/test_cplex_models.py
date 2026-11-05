# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from pathlib import Path
import sys

import pytest

from .test_model_base import BaseTestModel

try:
    import cplex
    from benderslib.solvers import Cplex

    cplex_available = True
except ImportError:
    cplex_available = False


pytestmark = pytest.mark.skipif(
    (3, 13) <= sys.version_info < (3, 14),
    reason="GitHub Actions failed with CPLEX on Python 3.13.",
)


@pytest.mark.skipif(not cplex_available, reason="CPLEX is not installed")
class TestCplexModels(BaseTestModel):
    @pytest.fixture
    def model_pair(self, model_name):
        models = []
        try:
            for _ in range(2):
                model = cplex.Cplex()
                models.append(model)
                model.set_log_stream(None)
                model.set_results_stream(None)
                model.read(str(Path(__file__).with_name(f"{model_name}.lp")))
                model.parameters.timelimit.set(30)
            yield tuple(models)
        finally:
            for model in models:
                model.end()

    @pytest.fixture
    def solver_class(self):
        return Cplex

    def solve_direct(self, model):
        model.solve()
        status = model.solution.status
        assert model.solution.get_status() in {status.optimal, status.MIP_optimal}
        return model.solution.get_objective_value()

    def snapshot_model(self, model):
        names = model.variables.get_names()
        types = (
            ["C"] * len(names) if model.get_problem_type() == model.problem_type.LP
            else model.variables.get_types()
        )
        variables = dict(zip(names, zip(
            model.variables.get_lower_bounds(), model.variables.get_upper_bounds(),
            [kind != "C" for kind in types], model.objective.get_linear(),
        )))
        constraints = []
        for name, row, sense, bound in zip(
            model.linear_constraints.get_names(), model.linear_constraints.get_rows(),
            model.linear_constraints.get_senses(), model.linear_constraints.get_rhs(),
        ):
            assert sense in {"L", "G", "E"}, name
            coefficients = {names[i]: coef for i, coef in zip(row.ind, row.val)}
            lhs = bound if sense in {"G", "E"} else -float("inf")
            rhs = bound if sense in {"L", "E"} else float("inf")
            constraints.append((name, coefficients, lhs, rhs))
        return variables, constraints, model.objective.get_offset()
