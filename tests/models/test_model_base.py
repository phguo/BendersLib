# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import math

import pytest

from benderslib import (
    AnnotatedBenders, BendersParams, ClassicalBenders, CombinatorialBenders, CST,
)


MODEL_CASES = [
    pytest.param("bd_transport", ["x11", "x12"], 22.0, ClassicalBenders, id="bd_transport"),
    pytest.param("bd_facility", ["open1", "open2"], 21.0, ClassicalBenders, id="bd_facility"),
    pytest.param("bd_production", ["capacity"], 19.0, ClassicalBenders, id="bd_production"),
    pytest.param(
        "bd_flow",
        ["open_sa", "open_at", "open_sb", "open_bt"],
        10.0,
        ClassicalBenders,
        id="bd_flow",
    ),
    pytest.param(
        "cbd_assignment", ["open1", "open2"], 12.0,
        CombinatorialBenders, id="cbd_assignment",
    ),
    pytest.param(
        "cbd_batch", ["enable1", "enable2"], 9.0,
        CombinatorialBenders, id="cbd_batch",
    ),
]


class BaseTestModel:
    """Compare native and decomposed solves of the same static model."""

    @pytest.fixture
    def model_pair(self, model_name):
        """Return two fresh models loaded from the same LP file."""
        raise NotImplementedError

    @pytest.fixture
    def solver_class(self):
        raise NotImplementedError

    def solve_direct(self, model):
        """Require native optimality and return the original objective value."""
        raise NotImplementedError

    def snapshot_model(self, model):
        """Return (variables, constraints, objective_offset) before solving.

        Variables map names to (lb, ub, is_integer, objective_coefficient).
        Constraints contain (name, coefficient_dict, lhs, rhs) tuples.
        """
        raise NotImplementedError

    def check_solution(self, snapshot, solution, objective):
        variables, constraints, offset = snapshot
        assert set(solution) == set(variables)
        for name, (lb, ub, integer, _) in variables.items():
            value = solution[name]
            assert math.isfinite(value), name
            assert lb - 1e-6 <= value <= ub + 1e-6, name
            if integer:
                assert value == pytest.approx(round(value), abs=1e-6, rel=0), name
        for name, coefficients, lhs, rhs in constraints:
            activity = sum(coef * solution[var] for var, coef in coefficients.items())
            assert lhs - 1e-6 <= activity <= rhs + 1e-6, name
        recomputed = offset + sum(
            data[3] * solution[name] for name, data in variables.items()
        )
        assert recomputed == pytest.approx(objective, abs=1e-6, rel=1e-7)

    @pytest.mark.parametrize("model_name,master_vars,expected_obj,benders", MODEL_CASES)
    def test_benders_matches_direct(
        self, model_name, master_vars, expected_obj, benders, model_pair, solver_class
    ):
        direct_model, benders_model = model_pair
        snapshot = self.snapshot_model(benders_model)
        direct_obj = self.solve_direct(direct_model)
        assert direct_obj == pytest.approx(expected_obj, abs=1e-6, rel=1e-7)

        bd = AnnotatedBenders(
            benders_model,
            solver=solver_class,
            complicating_vars=master_vars,
            benders=benders,
            params=BendersParams(
                tol_abs=1e-7, tol_rel=1e-9, time_limit=30, iter_limit=500
            ),
        )
        bd.solve()
        result = bd.result
        assert result.status == CST.OPTIMAL
        assert result.obj == pytest.approx(expected_obj, abs=1e-6, rel=1e-7)
        assert result.obj == pytest.approx(direct_obj, abs=1e-6, rel=1e-7)
        self.check_solution(snapshot, result.solution, result.obj)
        if model_name == "bd_facility" or benders is CombinatorialBenders:
            assert result.n_feas_cuts > 0
        if benders is CombinatorialBenders:
            assert result.n_opt_cuts > 0
