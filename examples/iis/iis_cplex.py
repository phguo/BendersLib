# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
CPLEX IIS
=======================================

.. currentmodule:: benderslib.solvers

"""

# %%
# Using :meth:`Cplex.compute_iis` to compute conflicting variables.

from benderslib.solvers import Cplex

import cplex


def make_sub_problem():
    model = cplex.Cplex()
    model.set_problem_name('InfeasibleExample')

    model.variables.add(obj=[0, 0], lb=[0, 0], ub=[5, 5], types=['I', 'I'], names=['x', 'y'])

    model.linear_constraints.add(
        lin_expr=[
            cplex.SparsePair(ind=['x'], val=[1.0]),
            cplex.SparsePair(ind=['y'], val=[1.0]),
            cplex.SparsePair(ind=['x', 'y'], val=[1.0, 1.0])
        ],
        senses=['G', 'G', 'L'],
        rhs=[5.0, 5.0, 9.0],
        names=['c1', 'c2', 'c3']
    )

    return model


if __name__ == '__main__':
    sub = make_sub_problem()

    # For simplicity, we directly use the Cplex solver interface from BendersLib.
    # Typically, this should be wrapped in the SubProblem class like SubProblem(Cplex(...)).
    sub_problem_solver = Cplex(sub)

    sub_problem_solver.solve()
    iis_vars = sub_problem_solver.compute_iis()
    print("Variables involved in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: cplex, iis
