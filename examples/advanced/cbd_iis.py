# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Combinatorial Benders Decomposition (IIS)
=========================================

This example demonstrates how to use the Combinatorial Benders decomposition method
with customized Benders cuts.
"""

# %%
# Define the original problem.

from benderslib import AnnotatedBenders, CombinatorialBenders, NoGoodFC, MasterProblem, SubProblem
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB
import matplotlib.pyplot as plt


def make_original_problem():
    # The problem is constructed such that the IIS involves only a few complicating variables.
    model = Model()

    n_vars = 9
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)

    # Constraint 1: All subproblem variables must be one
    model.addConstrs((y[i] == 1 for i in range(n_vars)), name="sub")
    # Constraint 2: But, part of the subproblem variables must be smaller than its first-stage counterpart
    model.addConstrs((y[i] <= x[i] for i in range(int(n_vars))), name="link")

    # Objective: minimize the number of non-zero first-stage variables, second-stage has no objective
    model.setObjective(x.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    complicating_vars = [v.VarName for v in x.values()]
    return model, complicating_vars


# %%
# Define stronger customized Benders feasibility cut using IIS.

def cut_generator(master_problem: MasterProblem, sub_problem: SubProblem):
    """
    Generate a stronger feasibility cut using the
    Irreducible Infeasible Subsystem (IIS) of the subproblem.
    Though `master_problem` is not used,
    it is required as a placeholder for the callback function.
    """

    # Compute the IIS of the subproblem
    sp = sub_problem.model
    sp.computeIIS()
    # Save IIS to file
    # sp.write("subproblem.ilp")

    # Get the names of the variables in the IIS
    # v.IISLB and v.IISUB can be either 0 (False) or 1 (True),
    # indicating whether the LB or UB is part of the IIS.
    iis_vars = [v.VarName for v in sp.getVars() if v.IISLB or v.IISUB]
    iis_var_values = master_problem.get_var_values(iis_vars)

    cut = NoGoodFC(iis_var_values)
    return [cut]


# %%
# Solve the problem using Gurobi.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

model.optimize()
print(f"Original Problem Obj: {model.ObjVal}")

# %%
# Solve the problem using Combinatorial Benders Decomposition + IIS-based cuts.

BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    # Customized feasibility cut generator
    feasibility_cut=cut_generator,
    benders=CombinatorialBenders,
)
# This example works well with the Branch-and-check method, try it!
BD.params.use_bnc = True

BD.solve()

# %%
# Solve the problem using Combinatorial Benders Decomposition + Naive cuts.

BD_ = AnnotatedBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=CombinatorialBenders,
)
# This example works well with the Branch-and-check method, try it!
BD_.params.use_bnc = True

BD_.solve()

# %%
# Compare the results.

print(f"Sol. Time (IIS vs Naive): {BD.result.runtime:.4f}, {BD_.result.runtime:.4f}")
print(f"Num. Cuts (IIS vs Naive): {BD.result.n_cuts}, {BD_.result.n_cuts}")

# plt.style.use('seaborn-v0_8')
# plt.figure(dpi=600)
# plt.bar(['IIS-based Cuts', 'Naive Cuts'], [BD.result.n_cuts, BD_.result.n_cuts])
# plt.ylabel('Number of Benders Cuts Added')
# plt.title('Comparison of Benders Cuts Added')
# plt.show()

# %%
#
# .. seealso::
#
#     * Tutorial of Combinatorial Benders Decomposition: :doc:`../../tutorials/cbd`
#     * This example uses the following classes: :class:`~benderslib.AnnotatedBenders`,
#       :class:`~benderslib.CombinatorialBenders`
#
# .. tags:: benders: combinatorial, solver: gurobi, deterministic, custom: cut, iis, branch-and-check
