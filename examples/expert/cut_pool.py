# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Cut Management
=========================================
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
# Define the cut management callback.

class CutPooling(CallbackBase):

    def __init__(self, ratio, frequency):
        self.ratio = ratio
        self.frequency = frequency

        self.cut_pool = []

    def _calc_violation(self, cut, theta_val, master_var_vals):
        # Calculate the violation level of the cut based on the current master solution.

        coefs = cut.coefs[:-1]
        vars = cut.vars[:-1]

        # let a cut be:             coefs * vars + theta >= rhs
        # it can be rearranged to:  theta >= rhs - coefs * vars
        # violation is defined as:  (rhs - coefs * var_vals) - theta_val

        violation = cut.rhs - sum(
            coef * master_var_vals[var_name] for var_name, coef in zip(vars, coefs)) - theta_val

        cut.violation = violation
        return violation

    def on_opti_cut_generated(self, context):

        # Add the optimality cuts generated in the current iteration to the cut pool.
        for cut in context.current_opti_cuts:
            self.cut_pool.append(cut)

        # Execute cut cleanup every specified number of iterations.
        if context.state.n_iter % self.frequency == 0:

            previous_cuts_num = len(context.master_problem.cuts)

            # Remove all optimality cute previously added.
            for cut in self.cut_pool:
                if cut.name in context.master_problem.cuts:
                    context.master_problem.remove_cut(cut.name)

            # Compare cut generated in the current iteration with the cut pool,
            # and determine cuts that are going to be added to the master problem based on the violation level.
            theta_val = context.master_problem.get_estimator_values()['theta']
            master_var_vals = context.master_problem.get_var_values(context.master_problem.complicating_vars)
            sorted_pool = sorted(
                self.cut_pool,
                key=lambda cut: self._calc_violation(cut, theta_val, master_var_vals),
                reverse=True
            )

            # Only add a specified portion of cuts with the highest violation level to the master problem.
            cut_num = int(self.ratio * len(sorted_pool))

            # context.current_opti_cuts is the list of cuts that are going to be
            # added to the master problem in the current iteration.
            context.current_opti_cuts = sorted_pool[:cut_num]

            current_cuts_num = len(context.current_opti_cuts)

            print(f"Iteration {context.state.n_iter}: "
                  f"Added {current_cuts_num} cuts to the master, "
                  f"to replace {previous_cuts_num} cuts from the master, "
                  f"total {len(self.cut_pool)} cuts in the pool.")


# %%
# Run with the callback.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

callback = CutPooling(ratio=0.9, frequency=20)
BD.register(callback)

BD.solve()
draw_curve(BD.result)

# %%
# .. hint::
#
#    This example demonstrate that the estimator (:math:`\theta`) can be approximated by a subset of
#    cuts. By only adding the most violated cuts to the master problem, we can reduce the number of
#    constraints in the master problem.
#
# Run without the callback.

BD_no_cm = AnnotatedBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

# BD_no_cm.solve()
# draw_curve(BD_no_cm.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#    - A brief introduction to :ref:`enhance_cut_management`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement
