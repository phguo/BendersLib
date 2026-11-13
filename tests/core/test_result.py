# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import json
import math
from dataclasses import asdict

import pytest

from benderslib import BendersResult
from benderslib.consts import BendersConsts as CST


def reject_constant(value):
    raise ValueError(f"Non-standard JSON constant: {value}")


@pytest.mark.parametrize("fields", [
    {},
    dict(status=CST.INFEASIBLE),
    dict(status=CST.TIMEOUT, obj=12.0, ub=12.0, n_sol=1,
         solution={"x": 2.0, "zero": 0.0}),
    dict(status=CST.OPTIMAL, obj=12.0, lb=12.0, ub=12.0,
         gap=0.0, gap_abs=0.0, n_sol=1, solution={"x": 2.0, "zero": 0.0}),
])
def test_save_result_states_as_strict_json(tmp_path, fields):
    result = BendersResult(**fields)
    before = asdict(result)
    filename = tmp_path / "result.json"

    result.save(filename)

    data = json.loads(filename.read_text(), parse_constant=reject_constant)
    expected = {
        k: None if isinstance(v, float) and not math.isfinite(v) else v
        for k, v in before.items()
    }
    expected["solution"] = {k: v for k, v in result.solution.items() if v != 0.0}
    assert data == expected
    assert asdict(result) == before


@pytest.mark.parametrize("nested", [False, True])
def test_save_converts_nonfinite_values_recursively_without_mutation(tmp_path, nested):
    values = [float("inf"), -float("inf"), float("nan"), 3.5]
    solution = dict(zip(["positive", "negative", "nan", "finite"], values))
    solution.update(zero=0.0, negative_zero=-0.0)
    result = BendersResult(
        lb_list=values.copy(), ub_list=values.copy(), obj_list=tuple(values),
        gap=float("nan"),
        solution={"scenario": solution, "empty": {}} if nested else solution,
    )
    filename = tmp_path / "result.json"

    result.save(filename)

    data = json.loads(filename.read_text(), parse_constant=reject_constant)
    for key in ("lb_list", "ub_list", "obj_list"):
        assert data[key] == [None, None, None, 3.5]
        original = getattr(result, key)
        assert original[0] == float("inf")
        assert original[1] == -float("inf")
        assert math.isnan(original[2])
        assert original[3] == 3.5
    assert isinstance(result.obj_list, tuple)
    assert data["gap"] is None
    assert math.isnan(result.gap)
    expected = dict(positive=None, negative=None, nan=None, finite=3.5)
    assert data["solution"] == ({"scenario": expected, "empty": {}} if nested else expected)
    assert solution["positive"] == float("inf")
    assert solution["negative"] == -float("inf")
    assert math.isnan(solution["nan"])
    assert solution["zero"] == solution["negative_zero"] == 0.0
