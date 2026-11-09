# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from unittest.mock import Mock

import pytest

from benderslib import SubProblems
from benderslib.errors import MismatchedProbabilityError


def scenarios():
    return [Mock(get_obj=Mock(return_value=cost)) for cost in (3.0, 7.0)]


@pytest.mark.parametrize("prob, expected", [
    (None, 5.0), ([2, 1], 13.0), ([0, 1], 7.0), ([-1, 1], 4.0), ([0, 0], 0.0),
])
def test_weighted_objective(prob, expected):
    subs = SubProblems(iter(scenarios()), prob=prob)
    assert subs.get_obj() == pytest.approx(expected)
    assert subs.prob == ([0.5, 0.5] if prob is None else prob)


@pytest.mark.parametrize("prob", [[], [1], [1, 1, 1]])
def test_mismatched_weights(prob):
    subs = scenarios()
    with pytest.raises(MismatchedProbabilityError, match="Length of <prob>"):
        SubProblems(subs, prob=prob)
    for sub in subs:
        sub.solve.assert_not_called()
        sub.get_obj.assert_not_called()


def test_weights_are_copied():
    prob = [2, 1]
    subs = SubProblems(scenarios(), prob=prob)
    prob.clear()
    assert subs.prob == [2, 1]
    assert subs.get_obj() == pytest.approx(13.0)
