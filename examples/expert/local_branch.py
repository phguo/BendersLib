# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Local Branching
===========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotatedBenders, CallbackBase
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB, LinExpr


def make_original_problem():
    model = Model("Original")

    n_vars = 20
    y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr_yz")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= 0.1 * i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_z")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Define the local branching callback.

class LocalBranchingCallback(CallbackBase):

    def __init__(self, radius, till_iter):
        self.radius = radius
        self.till_iter = till_iter

        self._pre_master_sol = None
        self._trust_region_added = False

        # Store local branching constraints, so that we can remove them later.
        self._pre_tr_cons = None

    def on_before_master_solve(self, context):

        if self._pre_master_sol and not self._trust_region_added:

            expr = LinExpr()
            for var_name in self._pre_master_sol:
                var = context.master_problem.model.getVarByName(var_name)

                # sum(1 - var_1) + sum(var_0) <= radius, where
                # var_1 are the variables that are 1 in the local branching center,
                # and var_0 are the variables that are 0 in the local branching center.
                # This is to restrict the Hamming distance between the current solution
                # and the local branching center.

                expr += (1 - var) if self._pre_master_sol[var_name] > 0.5 else var

            tr_cons = context.master_problem.model.addConstr(expr <= self.radius, name="trust_region")
            self._pre_tr_cons = tr_cons
            self._trust_region_added = True

    def _remove_trust_region(self, context):
        if self._pre_tr_cons:
            context.master_problem.model.remove(self._pre_tr_cons)
            self._pre_tr_cons = None
            self._trust_region_added = False

    def on_iteration_end(self, context):
        # Save solution as the local branching center
        self._pre_master_sol = context.master_problem.get_var_values()

        # Remove local branching constraints
        self._remove_trust_region(context)
        self._trust_region_added = False

        # Remove local branching after certain iterations
        if context.state.n_iter >= self.till_iter:
            self._trust_region_added = True


# %%
# Build the Benders decomposition instance.
# Here we set a small radius for local branching.
# Smaller radius means smaller feasible region for the master problem, which can lead to faster convergence.
# The local branching constraint is removed after specified iterations to ensure global convergence.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

callback = LocalBranchingCallback(2, till_iter=120)
BD.register(callback)

BD.solve()
draw_curve(BD.result)

# %%
# .. hint::
#
#     It can be observed that with local branching constraints, the time required to solve
#     the master problem is significantly reduced, since only a subregion is explored.
#     Solutions to the master problem obtained from a subregion can also generate useful cuts.
#
# Run without the local branching callback.

BD_no_tr = AnnotatedBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

# BD_no_tr.solve()
# draw_curve(BD_no_tr.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#    - A brief introduction to :ref:`enhance_local_branching`.
#    - **Examples**: :doc:`trust_region_bin`
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement
