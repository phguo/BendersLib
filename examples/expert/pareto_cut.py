# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Pareto-optimal Cut
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotatedBenders, CallbackBase, ClassicalOC
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
# Define the (approximate) Pareto-optimal cut callback.

class ParetoCut(CallbackBase):

    def __init__(self):
        # The core point will be iteratively updated.
        self.core_point = dict()

    def on_iteration_start(self, context):
        if context.state.n_iter <= 1:
            # No master solution is available at the beginning of the first iteration.
            return

        for var in context.current_comp_vals:

            # The approximate core point is updated as the average of
            # the current core point and the current master solution.
            # For the first iteration, the core point is simply set
            # to be the current master solution.

            if var in self.core_point:
                self.core_point[var] = (self.core_point[var] + context.current_comp_vals[var]) / 2
            else:
                self.core_point[var] = context.current_comp_vals[var]

        # Solve the Magnanti–Wong problem with the approximate core point.
        context.sub_problem.fix_vars(self.core_point)
        context.sub_problem.solve()

        # Generate an (approximate) Pareto-optimal cut.
        var_coefs = context.sub_problem.get_var_coefs(context.master_problem.complicating_vars)
        rhs = context.sub_problem.get_rhs()
        dual_values = context.sub_problem.get_dual_values()
        cut = ClassicalOC(context.master_problem.complicating_vars, var_coefs, dual_values, rhs)

        context.master_problem.add_cut(cut)

    def on_opti_cut_generated(self, context):
        if context.state.n_iter <= 1:
            # Use the master problem solution, instead of the core point,
            # to generate cuts in the first iteration, since the core point is not updated yet.
            return

        # Cut generation is taken over by the `on_iteration_start` callback,
        # so we clear the optimality cuts generated in the current iteration.
        context.current_opti_cuts = []


# %%
# This is an implementation of the *Algorithm 3* from the following paper.
# In the original Magnanti–Wong method, to obtain the Pareto-optimal cut,
# an additional optimization problem is required to be solved with the
# objective value of the original subproblem and a core
# point, which is usually difficult to be determined in practice.
# Papadakos provide a practical enhancement to the Magnanti–Wong method
# by using *approximate core points*, and the method does not require
# solution from the original subproblem, which is more efficient and easier to be implemented.
# However, it is worth noting that the cut generated can be not Pareto-optimal, relying
# on the choice of the core points.
#
# .. seealso::
#
#    Papadakos, N. (2008). Practical enhancements to the Magnanti–Wong method.
#    Operations Research Letters, 36(4), 444–449. https://doi.org/10.1016/j.orl.2008.01.005
#
# Run with the callback.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

callback = ParetoCut()
BD.register(callback)

BD.solve()
draw_curve(BD.result)

# %%
# .. hint::
#
#     With stronger cuts, in the early stage of the algorithm,
#     both the upper and lower bounds improve significantly.
#
# Run without the callback.

BD = AnnotatedBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

# BD.solve()
# draw_curve(BD.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#    - A brief introduction to :ref:`enhance_pareto_optimal_cut`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement
