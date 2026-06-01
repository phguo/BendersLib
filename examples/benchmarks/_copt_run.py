# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
_run
=======================================================

Run all the benchmarks.
"""

import os
import sys

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.path.abspath("."))

from copt_linear import run as run1
from copt_integer import run as run2
from copt_lbbd_location import run as run3
from _utils import draw

# %%
# Solve the benchmark problems using BendersLib.
# Easy instances are solved first.

# run3(solve_methods=['bd'], dry_run=False)
# run1(solve_methods=['bd'], dry_run=False)
# run2(solve_methods=['bd'], dry_run=False)

# %%
# Solve the benchmark problems using the monolithic models.
# Easy instances are solved first.

# run1(solve_methods=['de'], dry_run=False)
# run3(solve_methods=['de'], dry_run=False)
# run2(solve_methods=['de'], dry_run=False)

# %%
# Collect the data and draw the results.

# res1 = run1(dry_run=True)
# res2 = run2(dry_run=True)
# res3 = run3(dry_run=True)
# draw(
#     [res1, res2, res3],
#     ['Linear Subproblems', 'Integer Subproblems', 'Custom Solver and Cut'],
#     figure_name="copt"
# )
