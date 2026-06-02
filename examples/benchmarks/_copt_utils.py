# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
_utils
=======================================================

This file contains utility functions for :doc:`../benchmarks/index`.
"""

import json
import coptpy as cp
from coptpy import COPT, LinExpr


def _new_copt_model(name=None):
    env = cp.Envr()
    model = env.createModel(name)
    return model


def _copt_bound(value):
    if value == float("inf"):
        return COPT.INFINITY
    if value == -float("inf"):
        return -COPT.INFINITY
    return value


# %%
# Save COPT optimization result to a JSON file.

def save_copt_result(model, file_path, runtime=None):
    attrs = [
        "Status",
        "LpStatus",
        "MipStatus",
        "SimplexIter",
        "BarrierIter",
        "NodeCnt",
        "PoolSols",
        "TuneResults",
        "HasSol",
        "HasLpSol",
        "HasMipSol",
        "HasBasis",
        "HasDualFarkas",
        "HasPrimalRay",
        "IISCols",
        "IISRows",
        "IISSOSs",
        "IISIndicators",
        "HasIIS",
        "HasFeasRelaxSol",
        "IsMinIIS",
        "FeasRelaxObj",
        "HasSensitivity",
        "ObjVal",
        "ObjBound",
        "LpObjval",
        "BestObj",
        "BestBnd",
        "BestGap",
        "SolvingTime",
    ]

    result = {key: model.getAttr(key) for key in attrs}

    result["VariableValues"] = {var.getName(): var.X for var in model.getVars() if abs(var.X) > 0.0}
    result["SolutionInfo"] = {
        "Runtime": result.get("SolvingTime", runtime),
        "MIPGap": result.get("BestGap", None),
        "ObjVal": result.get("BestObj", None),
        "ObjBound": result.get("BestBnd", None),
        "Status": result.get("Status", None),
        "NodeCount": result.get("NodeCnt", None),
    }

    with open(file_path, "w") as f:
        json.dump(result, f, indent=4)


# %%
# Define the first-stage problem.

def first_stage_model(data, enforce_integer=False):
    # --- Get stage variables ---
    stage1_vars = [col for col, per in data['time_mapping']['col_period'].items() if per == 1]

    model = _new_copt_model(data['model_name'])

    # First-stage variables
    x = {}
    for var_name in stage1_vars:
        bounds = data['bounds'].get(var_name, {})
        lb = _copt_bound(bounds.get('LO', 0.0))
        ub = _copt_bound(bounds.get('UP', float('inf')))

        if enforce_integer:
            vtype = COPT.INTEGER
        else:
            vtype = COPT.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = COPT.INTEGER
            if var_name in data['binary_vars']:
                vtype = COPT.BINARY

        if abs(lb) < float('inf') and abs(ub) < float('inf'):
            if int(lb) == 0 and int(ub) == 1 and vtype == COPT.INTEGER:
                vtype = COPT.BINARY

        x[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=var_name)

    # reate constraints
    for row_name, row_type in data['rows'].items():
        if row_type == 'N':
            # Objective row
            continue

        row_period = data['time_mapping']['row_period'].get(row_name)

        if row_period == 1:
            # First-stage constraints
            expr = LinExpr()
            for col_name, coeff in data['columns'].items():
                if row_name in coeff and col_name in x:
                    expr += coeff[row_name] * x[col_name]

            rhs = data['rhs'].get(row_name, 0.0)
            if row_type == 'L':
                model.addConstr(expr <= rhs, name=row_name)
            elif row_type == 'G':
                model.addConstr(expr >= rhs, name=row_name)
            elif row_type == 'E':
                model.addConstr(expr == rhs, name=row_name)

    # Objective function
    obj_expr = LinExpr()
    obj_row_name = data['objective_name']

    # First-stage cost
    for col_name, coeff in data['columns'].items():
        if obj_row_name in coeff and col_name in x:
            obj_expr += coeff[obj_row_name] * x[col_name]

    model.setObjective(obj_expr, sense=COPT.MINIMIZE if data['objective_sense'] == 'MIN' else COPT.MAXIMIZE)

    return model, stage1_vars


# %%
# Define the second-stage problems for each scenario.

def second_stage_model(data):
    stage1_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 1}
    stage2_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 2}

    models = []
    probs = []
    env = cp.Envr()

    for scenario_name, s_data in data['scenarios'].items():
        probs.append(s_data['prob'])
        model = env.createModel(f"{data['model_name']}_{scenario_name}")

        # First-stage variables (as continuous)
        x = {}
        for var_name in stage1_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = _copt_bound(bounds.get('LO', 0.0))
            ub = _copt_bound(bounds.get('UP', float('inf')))
            x[var_name] = model.addVar(lb=lb, ub=ub, vtype=COPT.CONTINUOUS, name=var_name)

        # Second-stage variables
        y = {}
        for var_name in stage2_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = _copt_bound(bounds.get('LO', 0.0))
            ub = _copt_bound(bounds.get('UP', float('inf')))
            vtype = COPT.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = COPT.INTEGER
            if var_name in data['binary_vars']:
                vtype = COPT.BINARY
            y[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=f"{var_name}_{scenario_name}")

        # Create constraints
        for row_name, row_type in data['rows'].items():
            if row_type == 'N':
                continue

            row_period = data['time_mapping']['row_period'].get(row_name)

            if row_period == 2:
                expr = LinExpr()
                # Contribution from first-stage variables
                for col_name, coeff in data['columns'].items():
                    if row_name in coeff and col_name in x:
                        expr += coeff[row_name] * x[col_name]

                # Contribution from second-stage variables
                for col_name, coeff in data['columns'].items():
                    if row_name in coeff and col_name in y:
                        expr += coeff[row_name] * y[col_name]

                rhs = s_data['modi']['RHS'].get(row_name, data['rhs'].get(row_name, 0.0))
                constr_name = f"{row_name}_{scenario_name}"
                if row_type == 'L':
                    model.addConstr(expr <= rhs, name=constr_name)
                elif row_type == 'G':
                    model.addConstr(expr >= rhs, name=constr_name)
                elif row_type == 'E':
                    model.addConstr(expr == rhs, name=constr_name)

        # Objective function
        obj_expr = LinExpr()
        obj_row_name = data['objective_name']
        obj_modifications = s_data['modi'].get('OBJ', {})

        # Second-stage cost
        for col_name, coeff in data['columns'].items():
            if obj_row_name in coeff and col_name in y:
                # Use modified coefficient if available, otherwise use original
                obj_coeff = obj_modifications.get(col_name, coeff[obj_row_name])
                obj_expr += obj_coeff * y[col_name]

        model.setObjective(obj_expr, sense=COPT.MINIMIZE if data['objective_sense'] == 'MIN' else COPT.MAXIMIZE)
        models.append(model)

    return models, probs


# %%
# Define the deterministic equivalent model that combines all scenarios into a single large model.

def deterministic_equivalent_model(data, enforce_integer=False):
    stage1_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 1}
    stage2_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 2}

    model = _new_copt_model(data['model_name'])

    # First-stage variables
    x = {}
    for var_name in stage1_vars:
        bounds = data['bounds'].get(var_name, {})
        lb = _copt_bound(bounds.get('LO', 0.0))
        ub = _copt_bound(bounds.get('UP', float('inf')))

        if enforce_integer:
            vtype = COPT.INTEGER
        else:
            vtype = COPT.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = COPT.INTEGER
            if var_name in data['binary_vars']:
                vtype = COPT.BINARY

        if abs(lb) < float('inf') and abs(ub) < float('inf'):
            if int(lb) == 0 and int(ub) == 1 and vtype == COPT.INTEGER:
                vtype = COPT.BINARY

        x[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=var_name)

    # Second-stage variables
    y = {}
    scenarios = data['scenarios']
    for s_name in scenarios:
        y[s_name] = {}
        for var_name in stage2_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = _copt_bound(bounds.get('LO', 0.0))
            ub = _copt_bound(bounds.get('UP', float('inf')))
            vtype = COPT.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = COPT.INTEGER
            if var_name in data['binary_vars']:
                vtype = COPT.BINARY
            y[s_name][var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=f"{var_name}_{s_name}")

    # Create constraints
    for row_name, row_type in data['rows'].items():
        if row_type == 'N':
            # Objective row
            continue

        row_period = data['time_mapping']['row_period'].get(row_name)

        if row_period == 1:
            # First-stage constraints
            expr = LinExpr()
            for col_name, coeff in data['columns'].items():
                if row_name in coeff and col_name in x:
                    expr += coeff[row_name] * x[col_name]

            rhs = data['rhs'].get(row_name, 0.0)
            if row_type == 'L':
                model.addConstr(expr <= rhs, name=row_name)
            elif row_type == 'G':
                model.addConstr(expr >= rhs, name=row_name)
            elif row_type == 'E':
                model.addConstr(expr == rhs, name=row_name)

        elif row_period == 2:
            # Second-stage constraints
            for s_name, s_data in scenarios.items():
                expr = LinExpr()
                # First-stage variables in second-stage constraints
                for col_name, coeff in data['columns'].items():
                    if row_name in coeff and col_name in x:
                        expr += coeff[row_name] * x[col_name]

                # Second-stage variables
                for col_name, coeff in data['columns'].items():
                    if row_name in coeff and col_name in y[s_name]:
                        expr += coeff[row_name] * y[s_name][col_name]

                rhs = s_data['modi']['RHS'].get(row_name, data['rhs'].get(row_name, 0.0))
                constr_name = f"{row_name}_{s_name}"
                if row_type == 'L':
                    model.addConstr(expr <= rhs, name=constr_name)
                elif row_type == 'G':
                    model.addConstr(expr >= rhs, name=constr_name)
                elif row_type == 'E':
                    model.addConstr(expr == rhs, name=constr_name)

    # Objective function
    obj_expr = LinExpr()
    obj_row_name = data['objective_name']

    # First-stage cost
    for col_name, coeff in data['columns'].items():
        if obj_row_name in coeff and col_name in x:
            obj_expr += coeff[obj_row_name] * x[col_name]

    # Second-stage cost
    for s_name, s_data in scenarios.items():
        prob = s_data['prob']
        obj_modifications = s_data['modi'].get('OBJ', {})
        for col_name, coeff in data['columns'].items():
            if obj_row_name in coeff and col_name in y[s_name]:
                # Use modified coefficient if available, otherwise use original
                obj_coeff = obj_modifications.get(col_name, coeff[obj_row_name])
                obj_expr += prob * obj_coeff * y[s_name][col_name]

    model.setObjective(obj_expr, sense=COPT.MINIMIZE if data['objective_sense'] == 'MIN' else COPT.MAXIMIZE)

    return model
