# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Annotated Benders Decomposition
=======================================

This example automatically decomposes a mixed-integer programming problem into a master problem
and a subproblem based on the specified complicating variables, and then solves it using
the classical Benders decomposition method.
"""

# %%
# Define the original problem.

from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB


def make_original_problem():
    model = Model("Original")

    n_vars = 20
    y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr_yz")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_z")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Solve the problem using Gurobi.

model, complicating_vars = make_original_problem()
model.optimize()
print(f"Original Problem Obj: {model.ObjVal}")

# %%
# Solve the problem using Annotated Benders Decomposition.

BD = AnnotatedBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)

# # Another way: Manually decompose the model and create ClassicalBenders instance
# master_model, sub_model = AnnotatedBenders.decompose(model, Gurobi, complicating_vars, solver_model=True)
# BD = ClassicalBenders.from_models(master_model, Gurobi, sub_model, Gurobi, complicating_vars=complicating_vars)

# This example works well with the Branch-and-check method, try it!
BD.params.use_bnc = True

BD.solve()

draw_curve(BD.result)
print(f"Benders Decomposition Obj: {BD.result.obj}")

# %%
#
# .. seealso::
#
#     This example uses the following classes: :class:`~benderslib.AnnotatedBenders`, :class:`~benderslib.ClassicalBenders`
#
# .. tags:: benders: classical, solver: gurobi, deterministic, branch-and-check
