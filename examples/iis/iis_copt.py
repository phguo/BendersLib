# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Copt IIS
=======================================

.. currentmodule:: benderslib.solvers

"""

# %%
# Using :meth:`Copt.compute_iis` to compute conflicting variables.


from benderslib.solvers import Copt

try:
    import coptpy as cp
    from coptpy import COPT

    copt_available = True
except ImportError:
    copt_available = False


def make_sub_problem():
    env = cp.Envr()
    model = env.createModel(name='InfeasibleExample')

    x = model.addVar(lb=0, ub=5, vtype=COPT.INTEGER, name='x')
    y = model.addVar(lb=0, ub=5, vtype=COPT.INTEGER, name='y')

    model.addConstr(x >= 5, name='c1')
    model.addConstr(y >= 5, name='c2')
    model.addConstr(x + y <= 9, name='c3')

    return model


if __name__ == '__main__':
    if copt_available:
        sub = make_sub_problem()

        # For simplicity, we directly use the Copt solver interface from BendersLib.
        # Typically, this should be wrapped in the SubProblem class like SubProblem(Copt(...)).
        sub_problem_solver = Copt(sub)

        sub_problem_solver.solve()
        print("Optimization status :", sub_problem_solver.status)
        iis_vars = sub_problem_solver.compute_iis()
        print("Variables in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: copt, iis
