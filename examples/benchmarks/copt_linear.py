# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Linear Recourse (COPT)
=======================================================

.. seealso::

    See :doc:`linear` for the problem description, dataset, and algorithm details.
    This file is the COPT equivalent of that example, which uses Gurobi.
"""

# %%
# Import necessary packages.

import json
import os
import sys
import time
from itertools import product

from benderslib import LShaped, CallbackBase, BendersContext, CST
from benderslib.solvers import Copt
from benderslib import LShapedOCGen

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

    def __init__(self, lambda_, alpha, n, m):
        self.lambda_ = lambda_
        self.alpha = alpha
        self.n = n
        self.m = m
        self.core = None
        self.master_linear = None
        self.cut_generator = None
        self.lb_not_improved_iter_num = 0

    def on_sub_build(self, context: BendersContext):
        time_start = time.perf_counter()
        if self.master_linear is None:
            # Initialize the linear relaxation of the master problem.
            self.master_linear = context.master_problem.model.clone()
            self.master_linear.setVarType(self.master_linear.getVars(), 'C')

        if self.core is None:
            # Initialize the core point
            self.master_linear.solve()
            self.core = {v: self.master_linear.getVarByName(v).x for v in context.master_problem.complicating_vars}

        if self.cut_generator is None:
            # Initialize the cut generator.
            self.cut_generator = LShapedOCGen(context.master_problem, context.sub_problem, context.benders.params)

        cuts = []
        constrs = []
        current_obj = -float('Inf')

        for i in range(self.m):
            lambda_ = self.lambda_
            if self.lb_not_improved_iter_num >= self.n:
                self.lb_not_improved_iter_num = 0
                lambda_ = 1
            if self.lb_not_improved_iter_num >= self.n * 2:
                break

            # Update points
            point = dict()
            for var_name in self.core:
                x = self.master_linear.getVarByName(var_name).x
                self.core[var_name] = self.alpha * x + (1 - self.alpha) * self.core[var_name]
                point[var_name] = lambda_ * x + (1 - lambda_) * self.core[var_name]

            # Generate cuts
            context.sub_problem.fix_vars(point)
            context.sub_problem.prl_solve()
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
            if self.master_linear.objval > current_obj + 1e-4:
                current_obj = self.master_linear.objval
                self.lb_not_improved_iter_num = 0
            else:
                self.lb_not_improved_iter_num += 1

        # Detect constraint with positive slack
        cut_added_num = 0
        for cons, cut in zip(constrs, cuts):
            if cons.Slack < float('inf') and not cut in context.master_problem.optimality_cuts:
                context.master_problem.add_cut(cut)
                cut_added_num += 1

        # Add cuts to the master problem
        end_time = time.perf_counter()
        print(f"Generated <{cut_added_num}> cuts in <{(end_time - time_start):.2f}> seconds by InOut callback.")


# %%
# Solve the instances using different methods and save the results.
#
# .. note::
#
#     There are several implementation differences to :doc:`linear` for better performance:
#
#     - The branch-and-check option is turned off.
#     - Do not require the constraint slack to be negative to add the cut.

@limit_memory(limit_gb=14.5)
def solve(smps_files, instance_name, sample_num, time_limit, solve_methods, seed=1024):
    SMPS = SMPSReader(*smps_files, sample_num=sample_num, seed=seed)
    SMPS.parse()
    ins_file = f"./_copt_ins/{instance_name}_{sample_num}.json"
    SMPS.to_json(ins_file)
    with open(ins_file, 'r') as f:
        data = json.load(f)

    # Solve using deterministic equivalent
    if "de" in solve_methods:
        model = deterministic_equivalent_model(data, enforce_integer=True)
        model.setParam('TimeLimit', time_limit)
        model.solve()
        save_copt_result(model, f"./_copt_sol/{instance_name}_de_{sample_num}.json")
        bark(f"{instance_name}_{sample_num}", f"Solved using 'de' and COPT.")

    # Solve using Benders decomposition
    if "bd" in solve_methods:
        master_model, complicating_vars = first_stage_model(data, enforce_integer=True)
        sub_models, probs = second_stage_model(data)
        BD = LShaped.from_models(
            master_model=master_model,
            master_solver=Copt,
            sub_model=sub_models,
            sub_solver=Copt,
            complicating_vars=complicating_vars,
            prob=probs,
        )
        BD.register(InOut(lambda_=0.2, alpha=0.3, n=5, m=30))
        BD.params.parallel_sub = True
        # BD.params.use_bnc = True
        BD.params.time_limit = time_limit
        BD.params.theta_lb = 0
        BD.solve()
        BD.save(f"./_copt_sol/{instance_name}_bd_{sample_num}.json")
        bark(f"{instance_name}_{sample_num}", f"Solved using 'bd' and COPT.")


# %%
# .. rubric:: Set 1 Instances

def run(solve_methods=None, draw_result=False, dry_run=True):
    if solve_methods is None:
        solve_methods = ["de", "bd"]

    _dir = './set1'

    smps_files = {
        # Source: https://www4.uwsp.edu/math/afelt/slptestset/download.html

        "cargo": (_dir + "/cargo/4node.cor.base", _dir + "/cargo/4node.tim", _dir + "/cargo/4node.sto.32768"),
        "phone": (_dir + "/phone/phone.cor", _dir + "/phone/phone.tim", _dir + "/phone/phone.sto"),

        # Source: https://pages.cs.wisc.edu/~swright/stochastic/sampling/

        "lands": (_dir + "/lands/lands.cor", _dir + "/lands/lands.tim", _dir + "/lands/lands.sto"),
        "gbd": (_dir + "/gbd/gbd.cor", _dir + "/gbd/gbd.tim", _dir + "/gbd/gbd.sto"),
        "storm": (_dir + "/storm/storm.cor", _dir + "/storm/storm.tim", _dir + "/storm/storm.sto"),

        # Note: *cargo* and *storm* were originated from the same problem, but the data is different.
    }

    sample_nums = [
        64,
        128,
        256,
        512,
        1024,
    ]

    ins_names = []
    de_files = []
    bd_files = []
    ins_classes = []
    s_nums = []

    for (ins_class, smps_files), sample_num in product(smps_files.items(), sample_nums):
        ins_name = f"{ins_class}"
        de_file = f"./_copt_sol/{ins_name}_de_{sample_num}.json"
        bd_file = f"./_copt_sol/{ins_name}_bd_{sample_num}.json"

        ins_names.append(ins_name)
        de_files.append(de_file)
        bd_files.append(bd_file)
        ins_classes.append(ins_class)
        s_nums.append(sample_num)

        if not dry_run:
            solve(smps_files, ins_name, sample_num, time_limit=3600, solve_methods=solve_methods)

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
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lshaped`
#     * This example uses the following class: :class:`~benderslib.LShaped`
#     * Same instances using Gurobi as backend: :doc:`linear`
#
# .. tags:: benders: l-shaped, solver: copt, stochastic, branch-and-check, callback, enhancement
