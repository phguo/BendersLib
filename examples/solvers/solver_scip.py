# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
SCIP
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Scip` as a solver backend.

from benderslib import ClassicalBenders, AnnotatedBenders, CombinatorialBenders
from benderslib.solvers import Scip
from benderslib.utils import draw_curve

from pyscipopt import Model


def make_original_problem():
    model = Model("Original")

    n_vars = 10
    y = [model.addVar(vtype="I", name=f"y_{i}", ub=40) for i in range(n_vars)]
    z = [model.addVar(vtype="C", name=f"z_{i}", ub=40) for i in range(n_vars)]

    # Workaround for incorrect dual values of bound constraints in SCIP
    # dummy = model.addVar(vtype="C", name="dummy", ub=0, lb=0, obj=0)

    model.setObjective(2 * sum(y) + 3 * sum(z), "minimize")

    model.addCons(sum(y) + sum(z) <= 50 * n_vars)

    model.addConss([2 * y[i] <= 2 * (i + 1) for i in range(n_vars)])
    model.addConss([2 * y[i] + z[i] >= i for i in range(n_vars)])
    model.addConss([3 * z[i] <= 15 for i in range(n_vars)])

    complicating_vars = [f"y_{i}" for i in range(n_vars)]
    return model, complicating_vars


def make_combination_problem():
    model = Model("Combination")
    n_vars = 5
    x = [model.addVar(name=f"x_{i}", vtype="B") for i in range(n_vars)]
    y = [model.addVar(name=f"y_{i}", vtype="B") for i in range(n_vars)]

    # Constraint 1: All subproblem variables must be one
    for i in range(n_vars):
        model.addCons(y[i] == 1, name=f"sub_{i}")
    # Constraint 2: But, part of the subproblem variables must be smaller than its first-stage counterpart
    for i in range(n_vars):
        model.addCons(y[i] <= x[i], name=f"link_{i}")

    # Objective: minimize the number of non-zero first-stage variables, second-stage has no objective
    model.setObjective(sum(x), "minimize")

    complicating_vars = [v.name for v in x]
    return model, complicating_vars


# %%
# Classical Benders decomposition.

model, _ = make_original_problem()
model.optimize()
model.freeTransform()

model, master_vars = make_original_problem()
BD = AnnotatedBenders(model, solver=Scip, complicating_vars=master_vars, benders=ClassicalBenders)
BD.solve()
draw_curve(BD.result)

# %%
# Combinatorial Benders decomposition.

model, master_vars = make_combination_problem()
model.optimize()
model.freeTransform()

BD = AnnotatedBenders(model, solver=Scip, complicating_vars=master_vars, benders=CombinatorialBenders)
BD.params.use_iis_cut = True
BD.bnc_solve()

# %%
#
# .. tags:: benders: classical, solver: scip, deterministic, branch-and-check, benders: combinatorial
