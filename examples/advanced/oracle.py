# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Oracle Mode
============================================

.. currentmodule:: benderslib

This example solves a capacitated facility location problem. The master problem
selects facilities, while an oracle checks capacity, assigns demand, and returns
Benders cuts in one step.
"""

# %%
# Define the master problem.

from benderslib import CombinatorialOC, MasterProblem, NoGoodFC, Oracle, OracleBenders
from benderslib.solvers import Gurobi

from gurobipy import GRB, Model, quicksum

FACILITIES = {
    "north": {"capacity": 6, "open_cost": 4, "shipping_cost": 3},
    "central": {"capacity": 4, "open_cost": 3, "shipping_cost": 1},
    "south": {"capacity": 3, "open_cost": 2, "shipping_cost": 2},
}
DEMAND = 6


def make_master_problem():
    model = Model("FacilityLocation")
    open_facility = {
        name: model.addVar(vtype=GRB.BINARY, name=f"open_{name}")
        for name in FACILITIES
    }
    model.setObjective(
        quicksum(FACILITIES[name]["open_cost"] * var for name, var in open_facility.items()),
        GRB.MINIMIZE,
    )
    model.update()
    return MasterProblem(Gurobi(model)), [var.VarName for var in open_facility.values()]


# %%
# Solve the complete facility location model directly.

def solve_original_problem():
    model = Model("FacilityLocationOriginal")
    open_facility = {
        name: model.addVar(vtype=GRB.BINARY, name=f"open_{name}")
        for name in FACILITIES
    }
    shipment = {
        name: model.addVar(lb=0, name=f"ship_{name}")
        for name in FACILITIES
    }

    model.addConstr(sum(shipment.values()) == DEMAND, name="demand")
    for name in FACILITIES:
        model.addConstr(
            shipment[name] <= FACILITIES[name]["capacity"] * open_facility[name],
            name=f"capacity_{name}",
        )

    model.setObjective(
        quicksum(FACILITIES[name]["open_cost"] * open_facility[name] for name in FACILITIES)
        + quicksum(FACILITIES[name]["shipping_cost"] * shipment[name] for name in FACILITIES),
        GRB.MINIMIZE,
    )

    model.optimize()
    return model


# %%
# Define the oracle logic. It receives the master problem directly, checks the
# available capacity, and returns ``(cuts, sub_obj, var_values)``.

def evaluate_facilities(master_problem):
    open_values = master_problem.get_var_values()
    selected = {
        f"open_{name}": round(open_values[f"open_{name}"])
        for name in FACILITIES
    }
    available_capacity = sum(
        FACILITIES[name]["capacity"] * selected[f"open_{name}"]
        for name in FACILITIES
    )

    if available_capacity < DEMAND:
        # The current combination cannot serve all demand.
        return [NoGoodFC(selected)], None, {}

    remaining_demand = DEMAND
    shipments = {}
    sub_obj = 0.0
    for name in sorted(FACILITIES, key=lambda item: FACILITIES[item]["shipping_cost"]):
        if not selected[f"open_{name}"]:
            continue
        shipped = min(remaining_demand, FACILITIES[name]["capacity"])
        shipments[f"ship_{name}"] = shipped
        sub_obj += shipped * FACILITIES[name]["shipping_cost"]
        remaining_demand -= shipped
        if remaining_demand == 0:
            break

    return [CombinatorialOC(selected, sub_obj)], sub_obj, shipments


# %%
# Define a class-based oracle.


class FacilityOracle(Oracle):

    def __init__(self, master_problem, params):
        super().__init__(master_problem, params)
        self.calls = 0

    def evaluate(self):
        self.calls += 1
        return evaluate_facilities(self.master_problem)


# %%
# Solve with the class-based oracle and Branch-and-check.

# original_model = solve_original_problem()

master_problem, complicating_vars = make_master_problem()
benders = OracleBenders(master_problem, FacilityOracle, complicating_vars)

# Function-based oracle can also be used:
# benders = OracleBenders(master_problem, evaluate_facilities, complicating_vars)

benders.params.use_bnc = True
benders.solve()

# %%
# .. seealso::
#
#    - Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#    - Manual of :ref:`oracle mode <manual_oracle>`
#    - This example uses the following classes: :class:`Oracle`, :class:`OracleBenders`
#
# .. tags:: benders: lbbd, benders: oracle, solver: gurobi, deterministic
