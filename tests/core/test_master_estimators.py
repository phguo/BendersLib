# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from unittest.mock import Mock

import pytest

from benderslib import MasterProblem
from benderslib.errors import BendersMasterError, ReservedVariableNameError


@pytest.mark.parametrize("name", ["theta", "theta_2", "theta_custom"])
@pytest.mark.parametrize("multiple", [False, True])
def test_reserved_variable_names_fail_before_adding_estimators(name, multiple):
    solver = Mock(_all_vars=["x", name, "theta_other"])
    master = MasterProblem(solver)
    original_estimators = master.estimators

    with pytest.raises(ReservedVariableNameError, match="rename these variables") as exc_info:
        master._add_estimators(multiple=multiple, prob=[0.25, 0.75] if multiple else None)

    assert isinstance(exc_info.value, BendersMasterError)
    assert exc_info.value.code == 3004
    assert exc_info.value.context["variable_names"] == [name, "theta_other"]
    assert exc_info.value.context["conflict_count"] == 2
    assert name in str(exc_info.value)
    assert "theta_other" in str(exc_info.value)
    solver.add_estimators.assert_not_called()
    assert master.estimators is original_estimators
    assert master.estimators == []


def test_many_conflicts_show_only_first_ten_names_and_total():
    conflicts = [f"theta_{i}" for i in range(100)]
    solver = Mock(_all_vars=["x", *conflicts])
    master = MasterProblem(solver)

    with pytest.raises(ReservedVariableNameError) as exc_info:
        master._add_estimators()

    assert exc_info.value.context == {"variable_names": conflicts[:10], "conflict_count": 100}
    assert "theta_9" in str(exc_info.value)
    assert "theta_10" not in str(exc_info.value)
    assert "conflict_count=100" in str(exc_info.value)
    solver.add_estimators.assert_not_called()


@pytest.mark.parametrize("multiple, prob, expected", [
    (False, None, ["theta"]),
    (True, [0.25, 0.75], ["theta_1", "theta_2"]),
])
def test_estimators_preserve_names_weights_and_bounds(multiple, prob, expected):
    solver = Mock(_all_vars=["x", "my_theta", "Theta"])
    master = MasterProblem(solver)

    master._add_estimators(multiple=multiple, prob=prob, lb=-5.0)

    solver.add_estimators.assert_called_once_with(expected, prob, -5.0)
    assert master.estimators == expected
