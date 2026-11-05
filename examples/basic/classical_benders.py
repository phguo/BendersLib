# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Simple Classical Benders Example
==================================

This example explicitly defines master problem and subproblem for Benders decomposition.
"""

# %%
# Define a simple MILP problem.

from benderslib import BendersParams, MasterProblem, SubProblem, ClassicalBenders
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB


def make_original_problem():
    model = Model("Original")

    x = model.addVar(name="x", vtype=GRB.INTEGER)
    y = model.addVar(name="y")
    z = model.addVar(name="z")

    model.setObjective(x + 2 * y)
    model.addConstr(x + y + z == 14)
    model.addConstr(x - y == 2)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    return model


# %%
# Define master problem and subproblem for Benders decomposition.

def make_master_problem():
    model = Model("Master")

    x = model.addVar(name="x", vtype=GRB.INTEGER)
    z = model.addVar(name="z")

    model.setObjective(x)

    model.update()
    return model, [x.VarName, z.VarName]


def make_sub_problem():
    model = Model("Sub")

    master_x = model.addVar(name="x")
    y = model.addVar(name="y")
    master_z = model.addVar(name="z")

    model.setObjective(2 * y)
    model.addConstr(master_x + y + master_z == 14)
    model.addConstr(master_x - y == 2)

    model.update()
    return model


# %%
# Solve the problem using Gurobi.

model = make_original_problem()
model.optimize()
print(f"Original Problem Obj: {model.ObjVal}")

# %%
# Solve the problem using Classical Benders Decomposition.

# Define master problem
master_model, complicating_vars = make_master_problem()

# Define subproblem
sub_model = make_sub_problem()

# Create and solve Benders Decomposition instance
BD = ClassicalBenders.from_models(master_model, Gurobi, sub_model, Gurobi, complicating_vars=complicating_vars)

# # An alternative way to create Benders Decomposition instance
# master_problem = MasterProblem(solver_backend=Gurobi(master_model))
# sub_problem = SubProblem(solver_backend=Gurobi(sub_model))
# BD = ClassicalBenders(master_problem, sub_problem, complicating_vars=complicating_vars)

# This example works well with the Branch-and-check method, try it!
# BD.params.use_bnc = True

BD.solve()
BD.save("benders_result.json")

print(f"Benders Decomposition Obj: {BD.result.obj}")

# %%
#
# .. seealso::
#
#     * Tutorial of Classical Benders Decomposition: :doc:`../../tutorials/classical`
#     * This example uses the following class: :class:`~benderslib.ClassicalBenders`
#     * Automated decomposition based on complicating variables: :doc:`annotated_benders`
#
# .. tags:: benders: classical, solver: gurobi, deterministic, branch-and-check
