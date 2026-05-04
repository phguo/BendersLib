# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Trust Region Method (L1 Norm)
==================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotatedBenders, CallbackBase
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
# Define the trust region callback.

class TrustRegionCallback(CallbackBase):

    def __init__(self, radius, till_iter):
        self.radius = radius
        self.till_iter = till_iter

        self._pre_master_sol = None
        self._trust_region_added = False

        # Store the auxiliary variables and constraints added for the trust region, so that we can remove them later.
        self._pre_aux_cons = []
        self._pre_aux_vars = []
        self._pre_tr_cons = None

    def on_before_master_solve(self, context):
        aux_vars = []

        if self._pre_master_sol and not self._trust_region_added:

            # Add a trust region constraint to restrict the master solution within
            # a certain radius from the trust region center (the best-known solution).
            # The distance is computed using L1 norm, which can be linearized
            # by introducing auxiliary variables and constraints.

            for var_name in self._pre_master_sol:
                var = context.master_problem.model.getVarByName(var_name)

                # The distance aux_var = |var - pre_master_sol[var_name]| is linearized.
                aux_var = context.master_problem.model.addVar(name=f"aux_{var_name}", lb=0)
                aux_cons_a = context.master_problem.model.addConstr(aux_var >= var - self._pre_master_sol[var_name])
                aux_cons_b = context.master_problem.model.addConstr(aux_var >= self._pre_master_sol[var_name] - var)

                aux_vars.append(aux_var)
                self._pre_aux_cons.append(aux_cons_a)
                self._pre_aux_cons.append(aux_cons_b)

            self._pre_tr_cons = context.master_problem.model.addConstr(sum(aux_vars) <= self.radius)
            self._pre_aux_vars.extend(aux_vars)

            self._trust_region_added = True

    def on_new_upper_bound(self, context):
        # Save best-known solution as the trust region center
        self._pre_master_sol = context.master_problem.get_var_values()

        # Remove trust region
        self._remove_trust_region(context)

    def on_iteration_end(self, context):
        # Remove trust region after certain iterations
        if context.state.n_iter >= self.till_iter:
            self._remove_trust_region(context)
            self._trust_region_added = True

    def _remove_trust_region(self, context):
        # Remove trust region constraints
        if self._pre_tr_cons:
            context.master_problem.model.remove(self._pre_tr_cons)
            self._pre_tr_cons = None

        # Remove auxiliary constraints
        if self._pre_aux_cons:
            context.master_problem.model.remove(self._pre_aux_cons)
            self._pre_aux_cons = []

        # Remove auxiliary variables
        if self._pre_aux_vars:
            context.master_problem.model.remove(self._pre_aux_vars)
            self._pre_aux_vars = []

        self._trust_region_added = False


# %%
# .. warning::
#
#     The lower bound of Benders decomposition is essentially the master problem objective value,
#     which is **monotonously non-decreasing** as more cuts are added.
#     Adding trust region constraints can break this monotonicity, leading to **early (incorrect) convergence**.
#     In some extreme cases (small radius), trust region constraints may even make the master problem infeasible,
#     causing the algorithm to fail.
#
#     Therefore, **trust region must be removed after certain iterations** to ensure global convergence.
#
# Run with the trust region callback.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

trust_region_callback = TrustRegionCallback(15, 80)
BD.register(trust_region_callback)

BD.solve()
draw_curve(BD.result)

# %%
# Run without the trust region callback.

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
#    - A brief introduction to :ref:`enhance_trust_region`.
#    - **Examples**: :doc:`trust_region_l1`, :doc:`trust_region_box`, :doc:`trust_region_bin`
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement
