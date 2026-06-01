# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Facility Location (COPT)
=======================================================

.. seealso::

    See :doc:`lbbd_location` for the problem description, dataset, and algorithm details.
    This file is the COPT equivalent of that example, which uses Gurobi.
"""

# %%
# Import necessary packages.

import json
import os
import sys
from itertools import product

from benderslib import LogicBasedBenders, MasterProblem
from benderslib.solvers import Copt

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.path.abspath("."))

from _utils import draw, collect_data, limit_memory, bark
from _copt_utils import save_copt_result, _new_copt_model
from lbbd_location import feasibility_cut_generator, generate_instance_data, SubProblemSolver

from coptpy import COPT, LinExpr


def quicksum(terms):
    expr = LinExpr()
    for term in terms:
        expr += term
    return expr


# %%
# Define the function to solve the **integer programming** formulation.

def deterministic_equivalent_model(instance_data, enable_reinforcement=True):
    I = instance_data["client_indices"]
    J = instance_data["facility_indices"]
    K = instance_data["vehicle_indices"]
    facility_opening_costs = instance_data["facility_opening_costs"]
    vehicle_use_cost = instance_data["vehicle_use_cost"]
    assignment_costs = instance_data["assignment_costs"]
    max_vehicle_distance = instance_data["max_vehicle_distance"]
    travel_distances = instance_data["travel_distances"]
    facility_capacities = instance_data["facility_capacities"]
    client_demands = instance_data["client_demands"]

    # Create a COPT model
    model = _new_copt_model("IP")

    # Variables
    p = {j: model.addVar(vtype=COPT.BINARY, name=f"p[{j}]") for j in J}
    z = {(j, k): model.addVar(vtype=COPT.BINARY, name=f"z[{j},{k}]") for j in J for k in K}
    x = {
        (i, j, k): model.addVar(vtype=COPT.BINARY, name=f"x[{i},{j},{k}]")
        for i in I for j in J for k in K
    }

    # Constraints
    # (1) Each client must be served by exactly one facility and one vehicle.
    for i in I:
        model.addConstr(quicksum(x[i, j, k] for j in J for k in K) == 1)

    # (2) The total distance traveled by a vehicle cannot exceed its limit.
    for j in J:
        for k in K:
            model.addConstr(
                quicksum(travel_distances[f"{i},{j}"] * x[i, j, k] for i in I) <= max_vehicle_distance * z[j, k])

    # (3) The total demand served by a facility cannot exceed its capacity.
    for j in J:
        model.addConstr(
            quicksum(client_demands[i] * x[i, j, k] for i in I for k in K) <= facility_capacities[j] * p[j])

    # (4) A vehicle can only be assigned to an open facility.
    for j in J:
        for k in K:
            model.addConstr(z[j, k] <= p[j])

    # (5) A client can only be served by an activated vehicle.
    for i in I:
        for j in J:
            for k in K:
                model.addConstr(x[i, j, k] <= z[j, k])

    # (6) Symmetry-breaking: vehicles at a site are used in sequential order.
    for j in J:
        for k in K:
            if k > 1:
                model.addConstr(z[j, k] <= z[j, k - 1])

    if enable_reinforcement:
        # (8) A plant cannot be open if no client is assigned to it.
        for j in J:
            model.addConstr(p[j] <= quicksum(x[i, j, k] for i in I for k in K))

        # (9) A plant cannot be open if no vehicle is assigned to it.
        for j in J:
            model.addConstr(p[j] <= quicksum(z[j, k] for k in K))

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            vehicle_use_cost * quicksum(z[j, k] for j in J for k in K) +
            quicksum(assignment_costs[f"{i},{j}"] * x[i, j, k] for i in I for j in J for k in K)
    )
    model.setObjective(objective, COPT.MINIMIZE)

    return model


# %%
# Define the **master problem** for Logic-based Benders decomposition.

def make_master_problem(instance_data, sub_relaxation=True):
    I = instance_data["client_indices"]
    J = instance_data["facility_indices"]
    facility_opening_costs = instance_data["facility_opening_costs"]
    vehicle_use_cost = instance_data["vehicle_use_cost"]
    assignment_costs = instance_data["assignment_costs"]
    max_vehicle_distance = instance_data["max_vehicle_distance"]
    travel_distances = instance_data["travel_distances"]
    facility_capacities = instance_data["facility_capacities"]
    client_demands = instance_data["client_demands"]
    k_bar = instance_data["max_vehicles_per_facility"]

    # Create a COPT model
    master_model = _new_copt_model("MP")

    # Variables
    p = {j: master_model.addVar(vtype=COPT.BINARY, name=f"p[{j}]") for j in J}
    x = {(i, j): master_model.addVar(vtype=COPT.BINARY, name=f"x[{i},{j}]") for i in I for j in J}
    V = {j: master_model.addVar(vtype=COPT.INTEGER, lb=0, ub=k_bar, name=f"V[{j}]") for j in J}

    # Constraints
    # (10) Each client is served by exactly one facility.
    for i in I:
        master_model.addConstr(quicksum(x[i, j] for j in J) == 1)

    # (11) Facility capacity limit.
    for j in J:
        master_model.addConstr(quicksum(client_demands[i] * x[i, j] for i in I) <= facility_capacities[j] * p[j])

    # (12) Upper bound on a single client's travel distance.
    for i, j in product(I, J):
        master_model.addConstr(travel_distances[f"{i},{j}"] * x[i, j] <= max_vehicle_distance)

    if sub_relaxation:
        # (13) Relaxation of the subproblem (lower bound on number of vehicles).
        for j in J:
            master_model.addConstr(
                V[j] * max_vehicle_distance >= quicksum(travel_distances[f"{i},{j}"] * x[i, j] for i in I))

    # (15) Customers can only be allocated to open facilities.
    for i, j in product(I, J):
        master_model.addConstr(x[i, j] <= p[j])

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            quicksum(assignment_costs[f"{i},{j}"] * x[i, j] for i, j in product(I, J)) +
            vehicle_use_cost * quicksum(V[j] for j in J)
    )
    master_model.setObjective(objective, COPT.MINIMIZE)

    complicating_vars = [xx.getName() for xx in x.values()]
    complicating_vars += [vv.getName() for vv in V.values()]
    return master_model, complicating_vars


# %%
# Solve the instances using different methods and save the results.
#
# .. note::
#
#     There are several implementation differences to :doc:`lbbd_location` for better performance:
#
#     - Do not generate optimality cuts, instead of using ``CombinatorialOCGen``.

@limit_memory(limit_gb=14.5)
def solve(meta_data, time_limit, solve_methods):
    num_clients, num_facilities, correlated, truck_distance_limit, truck_usage_cost, random_seed = meta_data
    instance_data = generate_instance_data(
        num_clients=num_clients,
        num_facilities=num_facilities,
        correlated=correlated,
        truck_distance_limit=truck_distance_limit,
        truck_usage_cost=truck_usage_cost,
        random_seed=random_seed
    )
    instance_name = (f"loc_{num_clients}_{num_facilities}_{correlated}_"
                     f"{truck_distance_limit}_{truck_usage_cost}_{random_seed}")

    # Save the instance data to a JSON file
    ins_file = f"./_copt_ins/{instance_name}.json"
    with open(ins_file, "w") as f:
        json.dump(instance_data, f, indent=4)

    # Load the instance data from the JSON file
    with open(ins_file, "r") as f:
        instance_data = json.load(
            f, object_hook=lambda d: {int(k) if k.isdigit() else k: v for k, v in d.items()})

    # Solve using deterministic equivalent
    if "de" in solve_methods:
        model = deterministic_equivalent_model(instance_data)
        model.setParam('TimeLimit', time_limit)
        model.solve()
        save_copt_result(model, f"./_copt_sol/{instance_name}_de.json")
        bark(f"{instance_name}", f"Solved using 'de' and COPT.")

    # Solve using Logic-based Benders Decomposition
    if "bd" in solve_methods:
        master_model, complicating_vars = make_master_problem(instance_data)
        master_problem = MasterProblem(Copt(master_model))
        master_problem._instance_data = instance_data
        subproblem_solver = SubProblemSolver(complicating_vars, instance_data)
        BD = LogicBasedBenders(
            master_problem=master_problem,
            sub_problem=subproblem_solver,
            complicating_vars=complicating_vars,
            feasibility_cut=feasibility_cut_generator,
            # Optimality cut is required for the Branch-and-check method,
            # as the subproblem can be feasible for some master node solutions.
            optimality_cut=lambda mp, sp: []
        )
        BD.params.use_bnc = True
        BD.solve()
        BD.save(f"./_copt_sol/{instance_name}_bd.json")
        bark(f"{instance_name}", f"Solved using 'bd' and COPT.")


def run(solve_methods=None, draw_result=False, dry_run=True):
    if solve_methods is None:
        solve_methods = ["de", "bd"]

    problem_sizes = [
        (20, 10),
        (30, 15),
        (40, 20),
    ]
    truck_params = [
        (50, 50),
        (50, 100),
        (70, 100),
        (70, 150),
        (100, 150),
        (100, 300)
    ]
    correlated_conditions = [
        True,
        False
    ]
    random_seeds = range(0, 1)

    ins_names = []
    de_files = []
    bd_files = []
    ins_classes = []
    sample_nums = []

    for (num_clients, num_facilities), (
            truck_distance_limit, truck_usage_cost), correlated, random_seed in product(
        problem_sizes, truck_params, correlated_conditions, random_seeds):
        meta_data = (
            num_clients, num_facilities, correlated, truck_distance_limit, truck_usage_cost, random_seed)

        ins_name = f"loc_{meta_data[0]}_{meta_data[1]}_{meta_data[2]}_{meta_data[3]}_{meta_data[4]}_{meta_data[5]}"
        de_file = f"./_copt_sol/{ins_name}_de.json"
        bd_file = f"./_copt_sol/{ins_name}_bd.json"
        ins_class = "loc"
        sample_num = None

        ins_names.append(ins_name)
        de_files.append(de_file)
        bd_files.append(bd_file)
        ins_classes.append(ins_class)
        sample_nums.append(sample_num)

        if not dry_run:
            solve(tuple(meta_data), time_limit=3600, solve_methods=solve_methods)

    data_points = collect_data(
        ins_names=ins_names,
        de_files=de_files,
        bd_files=bd_files,
        ins_classes=ins_classes,
        sample_nums=sample_nums,
    )

    if draw_result:
        draw([data_points], titles=['LBBD'])

    return data_points


if __name__ == "__main__":
    ...
    # run(solve_methods=['bd'], draw_result=False, dry_run=False)

# %%
#
# .. seealso::
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#     * This example uses the following class: :class:`~benderslib.LogicBasedBenders`
#     * Same instances using Gurobi as backend: :doc:`lbbd_location`
#
# .. tags:: benders: lbbd, solver: copt, deterministic, custom: subproblem, custom: cut, branch-and-check
