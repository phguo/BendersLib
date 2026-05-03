# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import pytest
import os
import sys
from .test_solver_base import BaseTestSolver

try:
    import cplex
    from benderslib.solvers import Cplex

    cplex_available = True
except ImportError:
    cplex_available = False

LP_FILE = os.path.join(os.path.dirname(__file__), "lp.lp")
UBD_LP_FILE = os.path.join(os.path.dirname(__file__), "lp_ubd.lp")

pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 13) and sys.version_info < (3, 14),
    reason="GitHub Actions failed with CPLEX on Python 3.13."
)


@pytest.mark.skipif(not cplex_available, reason="CPLEX is not installed")
class TestCplex(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        model = cplex.Cplex()
        model.read(LP_FILE)
        return Cplex(model)

    @pytest.fixture
    def infeasible_solver_instance(self):
        model = cplex.Cplex()
        model.read(LP_FILE)

        # c3: x1 + x2 <= 3
        model.linear_constraints.add(
            lin_expr=[[['x1', 'x2'], [1.0, 1.0]]],
            senses=['L'],
            rhs=[3],
            names=['c3']
        )

        return Cplex(model)

    @pytest.fixture
    def unbounded_solver_instance(self):
        model = cplex.Cplex()
        model.read(UBD_LP_FILE)
        return Cplex(model)
