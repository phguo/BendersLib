# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Integer Recourse (COPT)
=======================================================

.. seealso::

    See :doc:`integer` for the problem description, dataset, and algorithm details.
    This file is the COPT equivalent of that example, which uses Gurobi.
"""

# %%
# Import necessary packages.

import json
import os
import sys
import time

from benderslib import CallbackBase, BendersContext, CST, IntegerLShaped, LShapedOCGen, SubProblems
from benderslib.solvers import Copt

from coptpy import LinExpr

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.path.abspath("."))

from _utils import SMPSReader, draw, collect_data, limit_memory, bark
from _copt_utils import first_stage_model, second_stage_model, deterministic_equivalent_model, save_copt_result


def _cut_expr(model, cut):
    expr = LinExpr()
    for var_name, coef in zip(cut.vars, cut.coefs):
        expr.addTerm(model.getVarByName(var_name), coef)
    return expr


# %%
# Define a callback for the in-out stabilization.

class InOut(CallbackBase):

    def __init__(self, lambda_, alpha, delta, n, m, integer=False):
        self.lambda_ = lambda_
        self.alpha = alpha
        self.delta = delta

        self.n = n
        self.m = m

        self.integer = integer

        self.master_linear = None
        self.sub_linear = None
        self.cut_generator = None
        self.core = None
        self.lb_not_improved_iter_num = 0

        self.classical_cut_time = 0

    def on_sub_build(self, context: BendersContext):
        # Initialize required attributes for the callback.

        if self.sub_linear is None:
            sub_models = []
            for p in context.sub_problem:
                m = p.model.clone()
                m.setVarType(m.getVars(), 'C')
                sub_models.append(m)

            self.sub_linear = SubProblems([Copt(s) for s in sub_models])
            self.sub_linear.complicating_vars = context.master_problem.complicating_vars

            # Set theta_lb based on linear relaxation of the subproblems
            theta_lb = 0
            for sub in context.sub_problem:
                sub.model.solve()
                theta_lb += sub.model.objval

            theta_lb = theta_lb / len(sub_models)
            # Add a small margin to avoid numerical issues
            theta_lb -= abs(theta_lb) * 0.2
            context.benders.params.theta_lb = theta_lb
            est = context.master_problem.estimators[0]
            var = context.master_problem.model.getVarByName(est)
            var.lb = theta_lb
            print(f"InOut callback: set <params.theta_lb> to < {theta_lb:.2f} >.")

        if self.master_linear is None:
            if self.integer:
                self.master_linear = context.master_problem.model.clone()
            else:
                self.master_linear = context.master_problem.model.clone()
                self.master_linear.setVarType(self.master_linear.getVars(), 'C')

        if self.core is None:
            self.master_linear.solve()
            self.core = {v: self.master_linear.getVarByName(v).x for v in context.master_problem.complicating_vars}

        if self.cut_generator is None:
            self.cut_generator = LShapedOCGen(context.master_problem, self.sub_linear, context.benders.params)

        self._add_stabilization_cuts(context, m=self.m)

    def on_opti_cut_generated(self, context: BendersContext):
        t_ = time.perf_counter()

        self.sub_linear.fix_vars(context.current_comp_vals)
        self.sub_linear.prl_solve()
        cut = self.cut_generator.generate()[0]
        if not cut in context.master_problem.optimality_cuts:
            context.current_opti_cuts.append(cut)

        self.classical_cut_time += time.perf_counter() - t_

    def on_benders_end(self, context: BendersContext):
        print(f"InOut callback: time for classical cuts is < {self.classical_cut_time:.2f} > seconds.")

    def _add_stabilization_cuts(self, context: BendersContext, m):
        start_time = time.perf_counter()
        cuts = []
        constrs = []
        current_obj = -float('Inf')

        for i in range(m):
            lambda_ = self.lambda_
            delta_ = self.delta
            if self.lb_not_improved_iter_num >= self.n:
                self.lb_not_improved_iter_num = 0
                lambda_ = 1
                delta_ = 0
            if self.lb_not_improved_iter_num >= self.n * 2:
                break

            # Update points
            point = dict()
            for var_name in self.core:
                x = self.master_linear.getVarByName(var_name).x
                self.core[var_name] = self.alpha * x + (1 - self.alpha) * self.core[var_name]
                point[var_name] = lambda_ * x + (1 - lambda_) * self.core[var_name] + delta_

            # Generate cuts
            # The complicating variables are binary, i.e, x \in [0, 1] and integer.
            # COPT will raise an error if attempting to fix x \in [0, 1] to a value
            # greater than 1 (like 1.00001), so we must cap the point values at 1.
            point = {var_name: min(round(val, 1), 1) for var_name, val in point.items()}

            self.sub_linear.fix_vars(point)
            self.sub_linear.prl_solve()
            cut = self.cut_generator.generate()[0]

            # Add cuts
            expr = _cut_expr(self.master_linear, cut)
            # LShapedOCGen returns only >= cuts.
            assert cut.sense == CST.GE
            cons = self.master_linear.addConstr(expr >= cut.rhs)
            constrs.append(cons)
            cuts.append(cut)

            # Check lower bound improvement
            self.master_linear.solve()
            if self.master_linear.objval > current_obj + 1e-6:
                current_obj = self.master_linear.objval
                self.lb_not_improved_iter_num = 0
            else:
                self.lb_not_improved_iter_num += 1

        # Add cut without positive slack to the master problem
        cut_added_num = 0
        for cons, cut in zip(constrs, cuts):
            if cons.Slack <= float('inf') and not cut in context.master_problem.optimality_cuts:
                context.master_problem.add_cut(cut)
                cut_added_num += 1
            else:
                self.master_linear.remove(cons)

        end_time = time.perf_counter()
        print(f"InOut callback: generated <{cut_added_num}> cuts in < {(end_time - start_time):.2f} > seconds.")


# %%
# Solve the instances using different methods and save the results.
#
# .. note::
#
#     There are several implementation differences to :doc:`integer` for better performance:
#
#     - The estimator's lower bound is computed using the subproblem, rather than its linear relaxation.
#     - Classical cuts are added even when the gap is less than 0.005 in the callback.
#     - Values of complicating variables are processed by ``min(round(val, 1), 1)`` in the callback.
#     - Do not require the constraint slack to be negative to add the cut.
#     - The branch-and-check option is turned off for instances *sslp*.

@limit_memory(limit_gb=14.5)
def solve(smps_files, instance_name, time_limit, solve_methods):
    SMPS = SMPSReader(*smps_files)
    SMPS.parse()
    ins_file = f"./_copt_ins/{instance_name}.json"
    SMPS.to_json(ins_file)
    with open(ins_file, 'r') as f:
        data = json.load(f)

    # Solve using deterministic equivalent
    if "de" in solve_methods:
        model = deterministic_equivalent_model(data)
        model.setParam('TimeLimit', time_limit)
        model.solve()
        save_copt_result(model, f"./_copt_sol/{instance_name}_de.json")
        bark(f"{instance_name}", f"Solved using 'de' and COPT.")

    # Solve using Benders decomposition
    if "bd" in solve_methods:
        master_model, complicating_vars = first_stage_model(data)
        sub_models, probs = second_stage_model(data)
        BD = IntegerLShaped.from_models(
            master_model=master_model,
            master_solver=Copt,
            sub_model=sub_models,
            sub_solver=Copt,
            complicating_vars=complicating_vars,
            prob=probs,
        )

        if "sslp" in instance_name:
            # The SSLP instances have negative objective values,
            # so we need to set a negative value to `theta_lb`.
            # A stronger `theta_lb` is provided in the callback.
            BD.params.theta_lb = -1e3
            BD.register(InOut(lambda_=0.2, alpha=0.3, delta=0.2, n=5, m=100, integer=True))

        if "smkp" in instance_name:
            BD.params.use_bnc = True
            BD.register(InOut(lambda_=0.2, alpha=0.3, delta=0.2, n=5, m=100))

        BD.params.parallel_sub = True
        # BD.params.use_bnc = True
        BD.params.time_limit = time_limit
        BD.solve()
        BD.save(f"./_copt_sol/{instance_name}_bd.json")
        bark(f"{instance_name}", f"Solved using 'bd' and COPT.")


# %%
# .. rubric:: Set 2 Instances

def run(solve_methods=None, draw_result=False, dry_run=True):
    if solve_methods is None:
        solve_methods = ["de", "bd"]

    _dir = './set2'

    smps_files = {
        # Source: https://www2.isye.gatech.edu/~sahmed/siplib/

        "sslp_1": (_dir + "/sslp/sslp_15_45_5.cor",
                   _dir + "/sslp/sslp_15_45_5.tim",
                   _dir + "/sslp/sslp_15_45_5.sto"),
        "sslp_2": (_dir + "/sslp/sslp_15_45_10.cor",
                   _dir + "/sslp/sslp_15_45_10.tim",
                   _dir + "/sslp/sslp_15_45_10.sto"),
        "sslp_3": (_dir + "/sslp/sslp_15_45_15.cor",
                   _dir + "/sslp/sslp_15_45_15.tim",
                   _dir + "/sslp/sslp_15_45_15.sto"),
        "sslp_4": (_dir + "/sslp/sslp_5_25_50.cor",
                   _dir + "/sslp/sslp_5_25_50.tim",
                   _dir + "/sslp/sslp_5_25_50.sto"),
        "sslp_5": (_dir + "/sslp/sslp_5_25_100.cor",
                   _dir + "/sslp/sslp_5_25_100.tim",
                   _dir + "/sslp/sslp_5_25_100.sto"),
        "sslp_6": (_dir + "/sslp/sslp_10_50_100.cor",
                   _dir + "/sslp/sslp_10_50_100.tim",
                   _dir + "/sslp/sslp_10_50_100.sto"),
        "sslp_7": (_dir + "/sslp/sslp_10_50_500.cor",
                   _dir + "/sslp/sslp_10_50_500.tim",
                   _dir + "/sslp/sslp_10_50_500.sto"),
        "sslp_8": (_dir + "/sslp/sslp_10_50_1000.cor",
                   _dir + "/sslp/sslp_10_50_1000.tim",
                   _dir + "/sslp/sslp_10_50_1000.sto"),
        "sslp_9": (_dir + "/sslp/sslp_10_50_2000.cor",
                   _dir + "/sslp/sslp_10_50_2000.tim",
                   _dir + "/sslp/sslp_10_50_2000.sto"),
    }

    smps_files.update({
        # Source: https://www2.isye.gatech.edu/~sahmed/siplib/

        f"smkp_{i}": (_dir + f"/smkp/smkp_{i}.cor",
                      _dir + f"/smkp/smkp_{i}.tim",
                      _dir + f"/smkp/smkp_{i}.sto")
        for i in range(1, 31)
    })

    ins_names = []
    de_files = []
    bd_files = []
    ins_classes = []
    s_nums = []

    for ins_name, smps_files_ in smps_files.items():
        ins_name = ins_name
        de_file = f"./_copt_sol/{ins_name}_de.json"
        bd_file = f"./_copt_sol/{ins_name}_bd.json"

        ins_names.append(ins_name)
        de_files.append(de_file)
        bd_files.append(bd_file)
        ins_classes.append(ins_name.split("_")[0])
        s_nums.append(int(smps_files_[0].split("_")[-1].split(".")[0]))

        if not dry_run:
            solve(smps_files_, ins_name, time_limit=3600, solve_methods=solve_methods)

    data_points = collect_data(
        ins_names=ins_names,
        de_files=de_files,
        bd_files=bd_files,
        ins_classes=ins_classes,
        sample_nums=s_nums,
    )

    if draw_result:
        draw(data_points)

    return data_points


if __name__ == "__main__":
    ...
    # run(solve_methods=['bd'], draw_result=False, dry_run=False)

# %%
#
# .. seealso::
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/ilshaped`
#     * This example uses the following class: :class:`~benderslib.IntegerLShaped`
#     * Same instances using Gurobi as backend: :doc:`integer`
#
# .. tags:: benders: integer l-shaped, solver: copt, stochastic, branch-and-check, callback, enhancement
