# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
L-shaped Method
============================================

This example solves a Two-stage Stochastic Programming problem using the L-shaped method.
The L-shaped method requires the second-stage problem to be a Linear Program.
"""

# %%
# Define the first-stage problem:

import random

from benderslib import MasterProblem, SubProblem, SubProblems, LShaped, BendersParams
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB


def first_stage_model(n_plants):
    model = Model("FirstStage")

    capacity = model.addVars(n_plants, vtype=GRB.INTEGER, name="capacity")
    model.setObjective(capacity.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [capacity[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem.
def second_stage_model(n_plants, scenarios, total_capacity):
    for s, demand in enumerate(scenarios):
        model = Model(f"SecondStage_{s}")

        # Complicating variables should have the **SAME names** as in the first-stage model
        capacity = model.addVars(n_plants, name="capacity")
        shortage = model.addVars(n_plants, lb=0, name="shortage")

        # Minimize shortage
        model.addConstrs((shortage[i] >= demand[i] - capacity[i] for i in range(n_plants)), name="shortage_constr")
        model.setObjective(shortage.sum())

        model.addConstr(capacity.sum() >= total_capacity, name="min_total_capacity_constr")

        yield model


# %%
# Define the deterministic equivalent problem for verification.
def deterministic_equivalent_model(n_plants, scenarios, probs, total_capacity):
    probs = [1 / len(scenarios) for _ in range(len(scenarios))] if probs[0] is None else probs

    model = Model('DE')

    capacity = model.addVars(n_plants, name="capacity")
    shortage = model.addVars(len(scenarios), n_plants, lb=0, name="shortage")

    # Objective
    model.setObjective(
        capacity.sum() +
        sum(probs[s] * sum(shortage[s, i] for i in range(n_plants)) for s, data in enumerate(scenarios)))

    # Constraints
    for s, demand in enumerate(scenarios):
        model.addConstrs(
            (shortage[s, i] >= demand[i] - capacity[i] for i in range(n_plants)),
            name=f"shortage_constr_s{s}"
        )

    model.addConstr(capacity.sum() >= total_capacity, name="min_total_capacity_constr")

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    return model


# %%
# Solve the problem using the deterministic equivalent (for clarity and verification).

# Data
random.seed(5)
n_plants = 5
n_scenarios = 150
total_capacity = 10
scenarios = [[random.randint(10, 220) for _ in range(n_plants)] for _ in range(n_scenarios)]
probs = [1.3 for _ in range(n_scenarios)]

# Deterministic equivalent solution
de_model = deterministic_equivalent_model(n_plants, scenarios, probs, total_capacity)
de_model.optimize()
print(f"Deterministic Equivalent Obj: {de_model.ObjVal:.4f}")

# %%
# Solve the problem using the single-cut L-shaped method.

# Create L-shaped solver
master_model, complicating_vars = first_stage_model(n_plants)
sub_models = second_stage_model(n_plants, scenarios, total_capacity)

master_problem = MasterProblem(solver_backend=Gurobi(master_model))
sub_problems = (SubProblem(solver_backend=Gurobi(sub_model)) for sub_model in sub_models)
sub_problems = SubProblems(sub_problems, prob=probs)

L = LShaped(
    master_problem=master_problem,
    sub_problem=sub_problems,
    complicating_vars=complicating_vars,
)
L.params.multi_opti_cut = True
# L.params.multi_feas_cut = True
L.solve()

# Another way to create L-shaped solver
master_model, complicating_vars = first_stage_model(n_plants)
sub_models = second_stage_model(n_plants, scenarios, total_capacity)

L = LShaped.from_models(
    master_model=master_model,
    master_solver=Gurobi,
    sub_model=sub_models,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
    prob=probs,
)

# This example works well with the Branch-and-check method, try it!
# L.params.use_bnc = True
L.params.parallel_sub = True

L.solve()
draw_curve(L.result)

# %%
#
# .. seealso::
#
#     * Tutorial of the L-shaped method: :doc:`../../tutorials/lshaped`
#     * This example uses the following class: :class:`~benderslib.LShaped`
#     * Example of integer L-shaped method: :doc:`ilshaped`
#
# .. tags:: benders: l-shaped, solver: gurobi, stochastic, branch-and-check, enhancement
