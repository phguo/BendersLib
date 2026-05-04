# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Cut from Master Solution Neighbor
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotatedBenders, CallbackBase, ClassicalOC, CST
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
# Define the callback to generate cuts from the neighbor of the current master solution.

class TwoCuts(CallbackBase):

    def __init__(self):
        self.best_known_sol = None

    def _calc_opti_violation(self, cut, theta_val, master_var_vals):
        # Calculate the violation level of the cut based on the current master solution.

        coefs = cut.coefs[:-1]
        vars = cut.vars[:-1]

        # let an optimality cut be: coefs * vars + theta >= rhs
        # it can be rearranged to:  theta >= rhs - coefs * vars
        # violation is defined as:  (rhs - coefs * var_vals) - theta_val

        violation = cut.rhs - sum(
            coef * master_var_vals[var_name] for var_name, coef in zip(vars, coefs)) - theta_val

        return violation

    def on_new_upper_bound(self, context):
        self.best_known_sol = context.master_problem.get_var_values(context.master_problem.complicating_vars)

    def _generate_cut(self, sol, context):
        context.sub_problem.fix_vars(sol)
        context.sub_problem.solve()

        if context.sub_problem.status != CST.OPTIMAL:
            # Optimality cut can be generated here, but we skip cut generation in this case for simplicity.
            return

        # Generate a cut from the neighbor of the current master solution.
        var_coefs = context.sub_problem.get_var_coefs(context.master_problem.complicating_vars)
        rhs = context.sub_problem.get_rhs()
        dual_values = context.sub_problem.get_dual_values()
        cut = ClassicalOC(context.master_problem.complicating_vars, var_coefs, dual_values, rhs)

        return cut

    def on_opti_cut_generated(self, context):
        if context.state.n_iter <= 1:
            return

        if not self.best_known_sol:
            return

        if context.state.n_iter > 40:
            # Only generate neighborhood cuts in the early stage of the algorithm.
            return

        for a, b in [(.4, .6), (.5, .5), (.6, .4)]:
            # Update the complicating variable values for generating cuts.
            sol = {
                var: a * self.best_known_sol[var] + b * context.current_comp_vals[var]
                for var in context.master_problem.complicating_vars
            }
            cut = self._generate_cut(sol, context)

            # Since the cut is not generated from the current master solution,
            # it is not guaranteed to be violated by the current master solution.
            # We can check the violation and only add the cut if it is violated.

            # Check whether the cut is violated.
            theta_val = context.master_problem.get_estimator_values()['theta']
            master_var_vals = context.master_problem.get_var_values(context.master_problem.complicating_vars)
            violation = self._calc_opti_violation(cut, theta_val, master_var_vals)

            if violation > 0:
                if not cut in context.master_problem.cuts.values():
                    if not cut in context.current_opti_cuts:
                        print(f"Iteration {context.state.n_iter}: "
                              f"Adding a cut with violation {violation:.4f} to the master problem.")
                        context.current_opti_cuts.append(cut)


# %%
# .. hint::
#
#    We do not need to **solve** the master problem to get cuts.
#
#    The cut is generated from the subproblem solved at a neighbor of the current master solution,
#    and it is added to the master problem only if it is violated by the current master solution.
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

callback = TwoCuts()
BD.register(callback)

# This example works well with the Branch-and-check method, try it!
# BD.params.use_bnc = True

BD.solve()
draw_curve(BD.result)

# %%
# Run without the callback.

BD = AnnotatedBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

# This example works well with the Branch-and-check method, try it!
# BD.params.use_bnc = True

# BD.solve()
# draw_curve(BD.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement, branch-and-check
