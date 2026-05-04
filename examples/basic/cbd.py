# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Combinatorial Benders Decomposition
=======================================

This example demonstrates how to use the Combinatorial Benders decomposition method.
This method is suitable for problems where the complicating variables are binary.
"""

# %%
# Define the original problem.
from benderslib import AnnotatedBenders, CombinatorialBenders
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB


def make_original_problem(has_sub_objective):
    """
    Creates a mixed-integer linear programming problem.
    The problem involves binary variables 'x', 'y', and continuous variables 'z'.
    The 'x' variables are chosen as the complicating variables.
    """
    model = Model()

    n_vars = 8
    # Master problem variables (complicating variables)
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    # Subproblem variables
    y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)
    z = model.addVars(n_vars, name="z", lb=0, vtype=GRB.CONTINUOUS)

    # Master problem constraint
    model.addConstr(x.sum() <= 5, "master_constr")
    # Linking constraints
    model.addConstrs((z[i] <= 10 * x[i] for i in range(n_vars)), name="linking_constr")
    # Subproblem constraints
    model.addConstr(y.sum() <= 8, "sub_constr_1")
    model.addConstr(z.sum() >= 15, "sub_constr_2")
    model.addConstrs((z[i] >= 2 * y[i] for i in range(n_vars)), name="sub_constr_3")

    # Objective function
    if has_sub_objective:
        # When the subproblem has its own objective, optimality cuts are generated.
        model.setObjective(x.sum() + y.sum() + z.sum(), sense=GRB.MINIMIZE)
    else:
        # When the subproblem has no objective, only feasibility cuts are generated.
        model.setObjective(x.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in x.values()]
    return model, complicating_vars


# %%
# Solve the problem using Gurobi.

# With subproblem objective
model, complicating_vars = make_original_problem(has_sub_objective=True)
# Without subproblem objective
# model, complicating_vars = make_original_problem(has_sub_objective=False)

# Solve with Gurobi
model.optimize()
print(f"Original Problem Obj: {model.ObjVal}")

# %%
# Solve the problem using Combinatorial Benders Decomposition.

# Using .from_models() method
# Decompose the original problem into master and subproblem
master_model, sub_model = AnnotatedBenders.decompose(
    original_problem=model,
    solver=Gurobi,
    master_vars=complicating_vars,
    solver_model=True
)
BD = CombinatorialBenders.from_models(
    master_model=master_model,
    master_solver=Gurobi,
    sub_model=sub_model,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
)

# Simpler way
# Master and Sub models are required to be re-defined,
# since they have been modified (by adding cuts) in the previous solve.
# model, complicating_vars = make_original_problem(has_sub_objective=True)
# BD = AnnotatedBenders(
#     original_problem=model,
#     solver=Gurobi,
#     complicating_vars=complicating_vars,
#     benders=CombinatorialBenders
# )

# This example works well with the Branch-and-check method, try it!
BD.params.use_bnc = True

BD.solve()

print(f"Benders Decomposition Obj: {BD.result.obj}")
draw_curve(BD.result)

# %%
#
# .. seealso::
#
#     * Tutorial of Combinatorial Benders Decomposition: :doc:`../../tutorials/cbd`
#     * This example uses the following classes: :class:`~benderslib.AnnotatedBenders`, :class:`~benderslib.CombinatorialBenders`
#     * Combinatorial Benders Decomposition with customized cut generator: :doc:`../advanced/cbd_iis`
#
# .. tags:: benders: combinatorial, solver: gurobi, deterministic, branch-and-check
