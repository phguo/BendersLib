# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Integer L-shaped Method
============================================

This example solves an integer Two-stage Stochastic Programming problem using the integer L-shaped method.
The integer L-shaped method is suitable for problems where the second-stage problem contains integer variables.
However, the complicating variables must be pure binary.
"""

# %%
# Define the first-stage problem.

import random

from benderslib import IntegerLShaped
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB


def first_stage_model(n_plants):
    model = Model("FirstStage")

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    model.setObjective(open.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [open[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem.

def second_stage_model(n_plants, scenarios, penalty):
    for s, demand in enumerate(scenarios):
        model = Model(f"SecondStage_{s}")

        # Complicating variables should have the **SAME names** as in the first-stage model
        open = model.addVars(n_plants, name="open")
        shortage = model.addVars(n_plants, vtype=GRB.BINARY, name="shortage")

        # Minimize shortage
        model.setObjective(shortage.sum() * penalty)

        # Shortage definition constraints
        model.addConstrs((shortage[i] >= demand[i] - open[i] for i in range(n_plants)), name="shortage")

        # Demand satisfaction constraints
        # model.addConstrs((demand[i] <= open[i] for i in range(n_plants)), name="demand_satisfaction")

        yield model


# %%
# Define the deterministic equivalent problem for verification.

def deterministic_equivalent_model(n_plants, scenarios, probs, penalty):
    probs = [1 / len(scenarios) for _ in range(len(scenarios))] if probs[0] is None else probs

    model = Model('DE')

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    shortage = model.addVars(len(scenarios), n_plants, vtype=GRB.BINARY, name="shortage")

    # Objective
    model.setObjective(
        open.sum() + penalty *
        sum(probs[s] * sum(shortage[s, i] for i in range(n_plants)) for s, data in enumerate(scenarios)))

    # Constraints
    for s, demand in enumerate(scenarios):
        # Shortage definition constraints
        model.addConstrs((shortage[s, i] >= demand[i] - open[i] for i in range(n_plants)), name=f"shortage_s{s}")
        # Demand satisfaction constraints
        # model.addConstrs((demand[i] <= open[i] for i in range(n_plants)), name=f"demand_satisfaction_s{s}")

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    return model


# %%
# Solve the problem using the deterministic equivalent.

# Data
random.seed(1)
n_plants = 7
n_scenarios = 5
penalty = 10
scenarios = [[random.choice([0, 1]) for _ in range(n_plants)] for _ in range(n_scenarios)]
probs = [1.3 for _ in range(n_scenarios)]

# Deterministic equivalent solution
de_model = deterministic_equivalent_model(n_plants, scenarios, probs, penalty)
de_model.optimize()
print(f"Deterministic Equivalent Obj: {de_model.ObjVal:.4f}")

# %%
# Solve the problem using the single-cut integer L-shaped method.

# Solver models
master_model, complicating_vars = first_stage_model(n_plants)
sub_models = second_stage_model(n_plants, scenarios, penalty)

# Integer L-shaped solver
L = IntegerLShaped.from_models(
    master_model=master_model,
    master_solver=Gurobi,
    sub_model=sub_models,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
    prob=probs,
)

# This example works well with the Branch-and-check method, try it!
L.params.use_bnc = True
L.params.parallel_sub = True

L.solve()
draw_curve(L.result)

# %%
# Solve the problem using the multi-cut integer L-shaped method.

# Solver models
master_model, complicating_vars = first_stage_model(n_plants)
sub_models = second_stage_model(n_plants, scenarios, penalty)

# Integer L-shaped solver
L = IntegerLShaped.from_models(
    master_model=master_model,
    master_solver=Gurobi,
    sub_model=sub_models,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
    prob=probs,
)

L.params.multi_opti_cut = True
# This example works well with the Branch-and-check method, try it!
L.params.use_bnc = True
L.params.parallel_sub = True

L.solve()
draw_curve(L.result)

# %%
#
# .. seealso::
#
#     * Tutorial of the integer L-shaped method: :doc:`../../tutorials/ilshaped`
#     * This example uses the following class: :class:`~benderslib.IntegerLShaped`
#     * Example of the L-shaped method: :doc:`lshaped`
#
# .. tags:: benders: integer l-shaped, solver: gurobi, stochastic, branch-and-check, enhancement
