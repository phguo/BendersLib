# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Cut Normalization
=======================
"""

# %%
# Prepare the problem for Benders decomposition.

import math

from benderslib import AnnotatedBenders, ClassicalBenders, CallbackBase
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve, normalize_cut

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

    # Huge coefficients to force the generation of cuts with large coefficients
    model.setObjective(2e5 * y.sum() + 3e5 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Define a callback to normalize Benders cuts if their norm exceeds a threshold.

class CutNormalization(CallbackBase):

    # This callback hooks into the cut generation process and checks the L2 norm
    # of the coefficient vector of each new optimality and feasibility cut. If the
    # norm is greater than a predefined ``MAX_NORM``, the cut's coefficients and
    # right-hand side are scaled down to meet the threshold. This can help
    # improve numerical stability in the master problem solver.

    def on_opti_cut_generated(self, context):
        for cut in context.current_opti_cuts:
            self._normalize(cut)

    def on_feas_cut_generated(self, context):
        for cut in context.current_feas_cuts:
            self._normalize(cut)

    def _normalize(self, cut):
        normalize_cut(cut, max_norm=1e5)

        # MAX_NORM = 1e5
        #
        # # Extract coefficients and constant term
        # a = cut.coefs
        #
        # # Calculate L2 norm
        # norm = math.sqrt(sum(c * c for c in a))
        #
        # if norm > MAX_NORM:
        #     scale = MAX_NORM / norm
        #
        #     # Modify the cut
        #     cut.coefs = [c * scale for c in cut.coefs]
        #     cut.rhs *= scale


# %%
# Use the callback in the Benders decomposition process.

model, complicating_vars = make_original_problem()
BD = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

# Comment out the normalization callback to see the difference in performance.
BD.register(CutNormalization())

# This example works well with the Branch-and-check method, try it!
BD.params.use_bnc = True

BD.solve()
draw_curve(BD.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#    - A brief introduction to :ref:`enhance_cut_normalization`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement, branch-and-check
