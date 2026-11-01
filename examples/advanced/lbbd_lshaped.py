# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
L-shaped Method by Logic-based Benders Decomposition
=====================================================

.. currentmodule:: benderslib

This example demonstrates how to implement the integer L-shaped method using Logic-Based Benders Decomposition in BendersLib.
It can be useful when one wants to customize a stochastic programming problem with multiple second-stage problems
and multiple estimator variables.
"""
import random

from benderslib import MasterProblem, LogicBasedBenders, SubProblems, SubProblem, IntegerLShapedOCGen, \
    LogicBasedSubProblem, CST
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB


# %%
# Define the first-stage problem.

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
        open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
        shortage = model.addVars(n_plants, vtype=GRB.BINARY, name="shortage")

        # Minimize shortage
        model.setObjective(shortage.sum() * penalty)

        # Shortage definition constraints
        model.addConstrs((shortage[i] >= demand[i] - open[i] for i in range(n_plants)), name="shortage")

        yield model


# %%
# Alternatively, define the second-stage problem using :class:`LogicBasedSubProblem` and :class:`SubProblems`.

class Sub(LogicBasedSubProblem):
    def __init__(self, complicating_vars, model: Model):
        self.model = model
        self.model.update()
        self.model.Params.OutputFlag = 0
        self.model.Params.LogToConsole = 0

        super().__init__(complicating_vars)

    def solve(self):
        for var_name, value in self.complicating_var_values.items():
            v = self.model.getVarByName(var_name)
            v.lb = value
            v.ub = value

        self.model.optimize()

        if self.model.status == GRB.OPTIMAL:
            self.status = CST.OPTIMAL
            self.obj = self.model.ObjVal
            self.var_values = {v.VarName: v.X for v in self.model.getVars()}
        elif self.model.status == GRB.INFEASIBLE:
            self.status = CST.INFEASIBLE
            self.obj = None
            self.var_values = {}
        else:
            raise Exception("Subproblem not solved to optimality or infeasibility.")


# %%
# Prepare components for Benders decomposition instance.

# Data
random.seed(1)
n_plants = 7
n_scenarios = 3
penalty = 2
scenarios = [[random.choice([0, 1]) for _ in range(n_plants)] for _ in range(n_scenarios)]
probs = [1 / len(scenarios) for _ in range(n_scenarios)]

# First-stage model
first_stage, complicating_vars = first_stage_model(n_plants)
first_stage_copy = first_stage.copy()

# Second-stage models
sub_models = list(second_stage_model(n_plants, scenarios, penalty))

# MasterProblem instance
master_problem = MasterProblem(Gurobi(first_stage))

# %%
# Solve the problem using Logic-Based Benders Decomposition.

# SubProblems instance
# sub_problem = SubProblems([SubProblem(Gurobi(m)) for m in sub_models], prob=probs)
# Alternative way using LogicBasedSubProblem
# sub_problem = SubProblems([Sub(complicating_vars, m) for m in sub_models], prob=probs)

# LBBD = LogicBasedBenders(
#     master_problem=master_problem,
#     sub_problem=sub_problem,
#     complicating_vars=complicating_vars,
#     optimality_cut=IntegerLShapedOCGen,
# )

LBBD = LogicBasedBenders.from_models(
    master_model=first_stage_copy,
    master_solver=Gurobi,
    sub_model=sub_models,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
    optimality_cut=IntegerLShapedOCGen,
    prob=probs,
)

# LBBD.params.multi_opti_cut = True
# This example works well with the Branch-and-check method, try it!
LBBD.params.use_bnc = True

LBBD.solve()

draw_curve(LBBD.result)

# %%
#
# .. seealso::
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#     * Manual of the Logic-based Benders Decomposition: :ref:`Logic-based Benders Decomposition <manual_logic_based_benders>`
#     * Tutorial of the L-shaped method: :doc:`../../tutorials/lshaped`
#     * This example uses the following class: :class:`LogicBasedBenders`
#     * Example of the L-shaped method: :doc:`../basic/lshaped`
#
# .. tags:: benders: lbbd, benders: l-shaped, solver: gurobi, stochastic, custom: subproblem, branch-and-check
