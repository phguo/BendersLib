# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Facility Location (Gurobi)
=======================================================

This example implements the Capacity- and Distance-Constrained Plant Location Problem. The problem
is solved with an integer programming model and Logic-based Benders Decomposition, respectively.
When using Logic-based Benders Decomposition, we demonstrate how to define a custom subproblem
solver and a custom cut generator.

.. seealso::

   * Fazel-Zarandi, M. M., & Beck, J. C. (2012). Using logic-based Benders decomposition to solve the
     capacity- and distance-constrained plant location problem. INFORMS Journal on Computing, 24(3),
     387–398. https://doi.org/10.1287/ijoc.1110.0458
"""

# %%
# Import necessary packages.

import json
import os
import sys
import random
from itertools import product

from benderslib import LogicBasedBenders, MasterProblem, CST, Cut, CombinatorialOCGen, LogicBasedSubProblem
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB, quicksum
from ortools.sat.python import cp_model

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.path.abspath("."))

from _utils import draw, collect_data, limit_memory


# %%
# Define the function to generate problem instance data.
#
# .. seealso::
#
#    See "Problem Set II" in Fazel-Zarandi and Beck (2012) for the instance generation procedure.

def generate_instance_data(
        num_clients, num_facilities, correlated, truck_distance_limit, truck_usage_cost, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed)

    # Sets
    client_indices = list(range(num_clients))
    facility_indices = list(range(num_facilities))
    max_vehicles_per_facility = num_clients // 4
    vehicle_indices = list(range(1, max_vehicles_per_facility + 1))

    # Parameters
    facility_capacities = {
        j: random.randint(50, 200) for j in facility_indices}
    facility_opening_costs = {
        j: facility_capacities[j] * (10 + random.randint(1, 5)) for j in facility_indices}
    travel_distances = {
        f"{i},{j}": random.randint(10, 60) for i, j in product(client_indices, facility_indices)}

    if correlated:
        assignment_costs = {f"{i},{j}": int(
            (travel_distances[f"{i},{j}"] - 10) / (60 - 10) * (90 - 10) + 10 + random.randint(-5, 5))
            for i, j in product(client_indices, facility_indices)}
    else:
        assignment_costs = {
            f"{i},{j}": random.randint(5, 95) for i, j in product(client_indices, facility_indices)}

    # This is set by us.
    client_demands = {i: random.randint(5, 15) for i in client_indices}

    instance_data = {
        # Sets
        "client_indices": client_indices,
        "facility_indices": facility_indices,
        "vehicle_indices": vehicle_indices,
        # Parameters: objective
        "facility_opening_costs": facility_opening_costs,
        "vehicle_use_cost": truck_usage_cost,
        "assignment_costs": assignment_costs,
        # parameters: constraints
        "max_vehicles_per_facility": max_vehicles_per_facility,
        "max_vehicle_distance": truck_distance_limit,
        "travel_distances": travel_distances,
        "facility_capacities": facility_capacities,
        "client_demands": client_demands,
    }
    return instance_data


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

    # Create a Gurobi model
    model = Model("IP")

    # Variables
    p = model.addVars(J, vtype=GRB.BINARY, name="p")
    z = model.addVars(J, K, vtype=GRB.BINARY, name="z")
    x = model.addVars(I, J, K, vtype=GRB.BINARY, name="x")

    # Constraints
    # (1) Each client must be served by exactly one facility and one vehicle.
    model.addConstrs((quicksum(x[i, j, k] for j in J for k in K) == 1 for i in I))

    # (2) The total distance traveled by a vehicle cannot exceed its limit.
    model.addConstrs(
        (quicksum(travel_distances[f"{i},{j}"] * x[i, j, k] for i in I) <= max_vehicle_distance * z[j, k]
         for j in J for k in K))

    # (3) The total demand served by a facility cannot exceed its capacity.
    model.addConstrs(
        (quicksum(client_demands[i] * x[i, j, k] for i in I for k in K) <= facility_capacities[j] * p[j]
         for j in J))

    # (4) A vehicle can only be assigned to an open facility.
    model.addConstrs((z[j, k] <= p[j] for j in J for k in K))

    # (5) A client can only be served by an activated vehicle.
    model.addConstrs((x[i, j, k] <= z[j, k] for i in I for j in J for k in K))

    # (6) Symmetry-breaking: vehicles at a site are used in sequential order.
    model.addConstrs((z[j, k] <= z[j, k - 1] for j in J for k in K if k > 1))

    if enable_reinforcement:
        # (8) A plant cannot be open if no client is assigned to it.
        model.addConstrs((p[j] <= quicksum(x[i, j, k] for i in I for k in K) for j in J))

        # (9) A plant cannot be open if no vehicle is assigned to it.
        model.addConstrs((p[j] <= quicksum(z[j, k] for k in K) for j in J))

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            vehicle_use_cost * quicksum(z[j, k] for j in J for k in K) +
            quicksum(assignment_costs[f"{i},{j}"] * x[i, j, k] for i in I for j in J for k in K)
    )
    model.setObjective(objective, GRB.MINIMIZE)

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

    # Create a Gurobi model
    master_model = Model("MP")

    # Variables
    p = master_model.addVars(J, vtype=GRB.BINARY, name="p")
    x = master_model.addVars(I, J, vtype=GRB.BINARY, name="x")
    V = master_model.addVars(J, vtype=GRB.INTEGER, lb=0, ub=k_bar, name="V")

    # Constraints
    # (10) Each client is served by exactly one facility.
    master_model.addConstrs((quicksum(x[i, j] for j in J) == 1 for i in I))

    # (11) Facility capacity limit.
    master_model.addConstrs(
        (quicksum(client_demands[i] * x[i, j] for i in I) <= facility_capacities[j] * p[j] for j in J))

    # (12) Upper bound on a single client's travel distance.
    master_model.addConstrs(
        (travel_distances[f"{i},{j}"] * x[i, j] <= max_vehicle_distance for i, j in product(I, J)))

    if sub_relaxation:
        # (13) Relaxation of the subproblem (lower bound on number of vehicles).
        master_model.addConstrs(
            (V[j] * max_vehicle_distance >= quicksum(travel_distances[f"{i},{j}"] * x[i, j] for i in I) for j in J))

    # (15) Customers can only be allocated to open facilities.
    master_model.addConstrs((x[i, j] <= p[j] for i, j in product(I, J)))

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            quicksum(assignment_costs[f"{i},{j}"] * x[i, j] for i, j in product(I, J)) +
            vehicle_use_cost * quicksum(V[j] for j in J)
    )
    master_model.setObjective(objective, GRB.MINIMIZE)

    master_model.update()
    complicating_vars = [xx.VarName for xx in x.values()]
    complicating_vars += [vv.VarName for vv in V.values()]
    return master_model, complicating_vars


# %%
#
# .. hint::
#
#    In the above master problem, constraint (13) is a relaxation of the subproblem.
#    **Adding subproblem relaxations expressed as master problem variables can significantly improve the convergence of
#    Logic-based Benders decomposition,** as discussed in:
#
#    * Hooker, J. N. (2019). Logic-based Benders decomposition for large-scale optimization.
#      In J. M. Velásquez-Bermúdez, M. Khakifirooz, & M. Fathi (Eds.), Large Scale Optimization
#      in Supply Chains and Smart Manufacturing: Theory and Applications (pp. 1–26).
#      Springer International Publishing. https://doi.org/10.1007/978-3-030-22788-3_1
#
# Define the **subproblem** solver for Logic-based Benders decomposition.
# In this example, the subproblem checks for feasibility. Benders feasibility cuts will be generated
# when the subproblem is infeasible (any facility is infeasible). When all the facilities are feasible,
# the optimum is reached.

class SubProblemSolver(LogicBasedSubProblem):
    def __init__(self, complicating_vars, instance_data):
        super().__init__(complicating_vars)

        self.instance_data = instance_data

    def solve(self):
        I = self.instance_data["client_indices"]
        J = self.instance_data["facility_indices"]
        vehicle_max_distance = self.instance_data["max_vehicle_distance"]
        travel_distances = self.instance_data["travel_distances"]
        k_bar = self.instance_data["max_vehicles_per_facility"]

        # Retrieve master problem solution
        facility_vehicle_num = {j: int(self.complicating_var_values[f"V[{j}]"]) for j in J}
        facility_clients = {j: [] for j in J}
        for i, j in product(I, J):
            if self.complicating_var_values[f"x[{i},{j}]"] > 0.5:
                facility_clients[j].append(i)

        # Determine the number of vehicles required for each facility
        facility_vehicle_num_req = {j: k_bar for j in J}
        for j in J:
            capacity = vehicle_max_distance
            items = [travel_distances[f"{i},{j}"] for i in facility_clients[j]]

            bin_num_ffd = _bin_packing_ffd(capacity, items)
            if bin_num_ffd > facility_vehicle_num[j]:
                bin_num_exact = _bin_packing_cp(capacity, items)
                if bin_num_exact > facility_vehicle_num[j]:
                    facility_vehicle_num_req[j] = bin_num_exact
                else:
                    facility_vehicle_num_req[j] = facility_vehicle_num[j]
            else:
                facility_vehicle_num_req[j] = facility_vehicle_num[j]

            if facility_vehicle_num_req[j] > facility_vehicle_num[j]:
                # ``facility_vehicle_num_req`` can be retrieved in the cut generator via ``sub_problem.var_values``
                self.status, self.obj, self.var_values = CST.INFEASIBLE, None, facility_vehicle_num_req
                return
        self.status, self.obj, self.var_values = CST.OPTIMAL, 0, facility_vehicle_num_req
        return


# %%
# The ``SubProblemSolver`` relies on solving bin packing problems to check feasibility.
#
# .. note::
#
#    **Bin Packing Problem**: Given a set of items with sizes and a set of bins with fixed capacity,
#    the bin packing problem aims to pack all items into the minimum number of bins without exceeding
#    the capacity of any bin.

def _bin_packing_ffd(capacity: float | int, items: list[float | int]):
    # A bin packing solver using first-fit decreasing (FFD) heuristic.
    bins = []

    for item in sorted(items, reverse=True):
        placed = False
        for b in bins:
            if sum(b) + item <= capacity:
                b.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])

    return len(bins)


def _bin_packing_cp(capacity: float | int, items: list[float | int]):
    # An exact bin packing solver using OR-Tools CP-SAT.
    model = cp_model.CpModel()

    n_items = len(items)
    max_bins = n_items

    # Variables
    # x[i, j] is 1 if item i is packed in bin j
    x = {}
    for i in range(n_items):
        for j in range(max_bins):
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")

    # y[j] is 1 if bin j is used
    y = [model.NewBoolVar(f"y_{j}") for j in range(max_bins)]

    # Constraints
    # Each item must be placed in exactly one bin
    for i in range(n_items):
        model.AddExactlyOne(x[i, j] for j in range(max_bins))

    # The amount packed in each bin cannot exceed its capacity
    for j in range(max_bins):
        model.Add(sum(items[i] * x[i, j] for i in range(n_items)) <= capacity * y[j])

    # Symmetry-breaking
    for j in range(max_bins - 1):
        model.Add(y[j] >= y[j + 1])

    # Objective: minimize the number of used bins
    model.Minimize(sum(y))

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return solver.ObjectiveValue()
    return max_bins


# %%
# Define the **feasibility cut generator** for Logic-based Benders decomposition.


def feasibility_cut_generator(master_problem, sub_problem):
    I = master_problem._instance_data["client_indices"]
    J = master_problem._instance_data["facility_indices"]

    # Retrieve decision variable values
    facility_vehicle_num = {j: int(sub_problem.complicating_var_values[f"V[{j}]"]) for j in J}
    facility_clients = {j: [] for j in J}
    for i, j in product(I, J):
        if sub_problem.complicating_var_values[f"x[{i},{j}]"] > 0.5:
            facility_clients[j].append(i)

    facility_vehicle_num_req = sub_problem.var_values

    cuts = []
    for j in J:
        if facility_vehicle_num_req[j] > facility_vehicle_num[j]:
            vars = [f"x[{i},{j}]" for i in facility_clients[j]] + [f"V[{j}]"]
            coefs = [1] * len(facility_clients[j]) + [-1]
            rhs = len(facility_clients[j]) - facility_vehicle_num_req[j]
            sense = CST.LE
            cut = Cut(
                vars=vars,
                coefs=coefs,
                rhs=rhs,
                sense=sense,
                ctype=CST.FEASIBILITY,
                name=f"FC",
            )
            cuts.append(cut)
            return cuts


# %%
# Solve the instances using different methods and save the results.

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
    ins_file = f"./_ins/{instance_name}.json"
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
        model.optimize()
        model.write(f"./_sol/{instance_name}_de.json")

    # Solve using Logic-based Benders Decomposition
    if "bd" in solve_methods:
        master_model, complicating_vars = make_master_problem(instance_data)
        master_problem = MasterProblem(Gurobi(master_model))
        master_problem._instance_data = instance_data
        subproblem_solver = SubProblemSolver(complicating_vars, instance_data)
        BD = LogicBasedBenders(
            master_problem=master_problem,
            sub_problem=subproblem_solver,
            complicating_vars=complicating_vars,
            feasibility_cut=feasibility_cut_generator,
            # Optimality cut is required for the Branch-and-check method,
            # as the subproblem can be feasible for some master node solutions.
            optimality_cut=CombinatorialOCGen,
        )
        BD.params.use_bnc = True
        BD.solve()
        BD.save(f"./_sol/{instance_name}_bd.json")


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
        de_file = f"./_sol/{ins_name}_de.json"
        bd_file = f"./_sol/{ins_name}_bd.json"
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
    # run(draw_result=True)

# %%
#
# .. seealso::
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#     * This example uses the following class: :class:`~benderslib.LogicBasedBenders`
#
# .. tags:: benders: lbbd, solver: gurobi, deterministic, custom: subproblem, custom: cut, branch-and-check
