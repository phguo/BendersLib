# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Stochastic Logic-Based Benders Decomposition
============================================

.. currentmodule:: benderslib

This example demonstrates how to implement a Logic-Based Benders Decomposition method for two-stage stochastic problems,
with custom subproblem solver using BendersLib.
"""

# %%
# Define the master problem.

import random

from benderslib import CST, MasterProblem, LogicBasedBenders, CombinatorialFCGen, CombinatorialOCGen
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB


def master_model(n_plants):
    model = Model("Master")

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    model.setObjective(open.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [open[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Use a simple function as subproblem solver.
# The input is a dictionary of complicating variable values.
# The output is a tuple:
# (:attr:`LogicBasedSubProblem.status`, :attr:`LogicBasedSubProblem.obj`, :attr:`LogicBasedSubProblem.var_values`).

def sub_solver(complicating_var_values):
    n_plants = len(complicating_var_values)
    random.seed(1)
    scenarios = [random.randint(0, n_plants) for _ in range(n_plants)]

    # Sub problem is feasible if it covers demand in all scenarios.
    for s in scenarios:
        if sum(complicating_var_values.values()) < s:
            return CST.INFEASIBLE, None, {}
    return CST.OPTIMAL, 0, {}


# %%
# Solve the problem using Logic-Based Benders Decomposition.

n_plants = 8
master_model, complicating_vars = master_model(n_plants)
master_model_copy = master_model.copy()

master_problem = MasterProblem(Gurobi(master_model))
LBBD = LogicBasedBenders(
    master_problem=master_problem,
    # Use the function defined above as a subproblem solver
    sub_problem=sub_solver,
    complicating_vars=complicating_vars,
    feasibility_cut=CombinatorialFCGen,
    # Optimality cut is required for the Branch-and-check method,
    # as the subproblem can be feasible for some master node solutions.
    optimality_cut=CombinatorialOCGen,
)
# This example works well with the Branch-and-check method, try it!
LBBD.params.use_bnc = True

LBBD.solve()

# %%
#
# .. seealso::
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#     * Manual of the Logic-based Benders Decomposition: :ref:`Logic-based Benders Decomposition <manual_logic_based_benders>`
#     * This example uses the following class: :class:`LogicBasedBenders`
#
# .. tags:: benders: lbbd, solver: gurobi, stochastic, custom: subproblem, branch-and-check
