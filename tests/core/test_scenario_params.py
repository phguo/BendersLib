# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from threading import get_ident
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from benderslib import (
    BendersParams, BendersSolver, CST, LogicBasedSubProblem,
    MasterProblem, SubProblem, SubProblems,
)


class LogicalSub(LogicBasedSubProblem):
    def solve(self):
        self.on_solve()
        self.status = CST.OPTIMAL


@pytest.mark.parametrize("kinds, collection", [
    (["ordinary"], False),
    (["logic"], False),
    (["ordinary", "ordinary"], True),
    (["logic", "logic"], True),
    (["ordinary", "logic"], True),
])
@pytest.mark.parametrize("parallel", [False, True])
@pytest.mark.parametrize("explicit_params", [False, True])
def test_shared_params_and_complicating_vars_during_solve(kinds, collection, parallel, explicit_params):
    members = [
        SubProblem(SimpleNamespace(model=None, status=CST.OPTIMAL), complicating_vars=["old"])
        if kind == "ordinary" else LogicalSub(["old"])
        for kind in kinds
    ]
    sub_problem = SubProblems(members) if collection else members[0]
    master = MasterProblem(SimpleNamespace(model=None))
    params = BendersParams(parallel_sub=parallel, parallel_threads=2, tol_abs=0.123) if explicit_params else None
    complicating_vars = ["x", "y"]

    def no_cuts(master, sub):
        return []

    benders = BendersSolver(master, sub_problem, complicating_vars, optimality_cut=no_cuts, params=params)
    shared = benders.params
    if explicit_params:
        assert shared is params
    else:
        shared.parallel_sub = parallel
        shared.parallel_threads = 2
    assert master.params is master.solver.params is sub_problem.params is shared
    assert master.complicating_vars is sub_problem.complicating_vars is complicating_vars

    main_thread = get_ident()

    def check_at_solve(sub):
        assert sub.params is shared
        assert sub.complicating_vars is complicating_vars
        backend = getattr(sub, "solver", None)
        if backend is not None:
            assert backend.params is shared
        assert (get_ident() != main_thread) == (collection and parallel)

    checks = []
    for sub in members:
        check = Mock(side_effect=lambda sub=sub: check_at_solve(sub))
        checks.append(check)
        if isinstance(sub, SubProblem):
            sub.solver.solve = check
        else:
            sub.on_solve = check

    sub_problem.solve()

    assert sub_problem.status == CST.OPTIMAL
    for check in checks:
        check.assert_called_once_with()
