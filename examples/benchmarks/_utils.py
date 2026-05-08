# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
_utils
=======================================================

This file contains utility functions for :doc:`../benchmarks/index`.
"""

import collections
import random
import json
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PLT_PARAM = {
    "font.family": "Arial",

    "font.size": 7,
    "axes.titlesize": 7,

    "ytick.major.size": 2,
    "ytick.major.width": .5,
    "ytick.labelsize": 7,

    "xtick.major.size": 2,
    "xtick.major.width": .5,
    "xtick.labelsize": 7,
}
plt.rcParams.update(PLT_PARAM)

import gurobipy as gp
from gurobipy import GRB


# %%
# Define a parser for SMPS files to extract the model data and scenario information.
#
# .. warning::
#
#    This is a simplified parser and may not cover all features of the SMPS format.

class SMPSReader:

    def __init__(self, cor_file_path=None, tim_file_path=None, sto_file_path=None, sample_num=None, seed=None):
        if seed is not None:
            random.seed(seed)

        self.cor_file_path = cor_file_path
        self.tim_file_path = tim_file_path
        self.sto_file_path = sto_file_path
        self.sample_num = sample_num

        # .cor
        self.model_name = ""
        self.objective_sense = "MIN"
        self.objective_name = ""
        # {row_name: row_type ('N', 'E', 'L', 'G')}
        self.rows = collections.OrderedDict()
        # {col_name: {row_name: value, ...}}
        self.columns = collections.defaultdict(dict)
        # {row_name: value}
        self.rhs = collections.defaultdict(float)
        # {col_name: {'type': 'LO', 'value': 0.0}}
        self.bounds = collections.defaultdict(dict)

        self.integer_vars = set()
        self.binary_vars = set()

        # .tim
        self.time_mapping = {}

        # .sto
        self.scenarios = {}

    def parse(self):
        self.parse_cor(self.cor_file_path)
        self.parse_tim(self.tim_file_path)
        self.parse_sto(self.sto_file_path)

    def parse_cor(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        self._parse_lines(lines)

    def parse_tim(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        self._parse_time(lines)

    def parse_sto(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        self._parse_sto(lines)

    def _parse_lines(self, lines):
        current_section = None
        is_integer_section = False

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('*'):
                continue

            fields = line.split()
            if not fields:
                continue

            if len(fields) <= 2 and fields[0] in ["NAME", "OBJSENSE", "ROWS", "COLUMNS", "RHS", "BOUNDS", "ENDATA"]:
                current_section = fields[0]
                if current_section == "ENDATA":
                    break
                continue

            if current_section == "NAME":
                if len(fields) > 1:
                    self.model_name = fields[1]

            elif current_section == "OBJSENSE":
                if fields[0].upper() == "MAX":
                    self.objective_sense = "MAX"

            elif current_section == "ROWS":
                self._parse_rows_section(fields)

            elif current_section == "COLUMNS":
                is_integer_section = self._parse_columns_section(fields, is_integer_section)

            elif current_section == "RHS":
                self._parse_rhs_section(fields)

            elif current_section == "BOUNDS":
                self._parse_bounds_section(fields)

    def _parse_rows_section(self, fields):
        row_type, row_name = fields[0], fields[1]
        self.rows[row_name] = row_type
        # The first 'N' is the objective row
        if row_type == 'N' and not self.objective_name:
            self.objective_name = row_name

    def _parse_columns_section(self, fields, is_integer_section):
        col_name = fields[0]

        if len(fields) > 1 and fields[1].upper() == "'MARKER'":
            if len(fields) > 2 and fields[2].upper() == "'INTORG'":
                return True
            elif len(fields) > 2 and fields[2].upper() == "'INTEND'":
                return False

        if is_integer_section:
            self.integer_vars.add(col_name)

        # COL_NAME  ROW_NAME1  VALUE1  [ROW_NAME2  VALUE2]
        if len(fields) >= 3:
            self.columns[col_name][fields[1]] = float(fields[2])
        if len(fields) >= 5:
            self.columns[col_name][fields[3]] = float(fields[4])

        return is_integer_section

    def _parse_rhs_section(self, fields):
        # RHS_NAME  ROW_NAME1  VALUE1  [ROW_NAME2  VALUE2]
        if len(fields) >= 3:
            self.rhs[fields[1]] = float(fields[2])
        if len(fields) >= 5:
            self.rhs[fields[3]] = float(fields[4])

    def _parse_bounds_section(self, fields):
        bound_type, bound_name, var_name = fields[0], fields[1], fields[2]
        value = float(fields[3]) if len(fields) > 3 else None

        if bound_type == "LO":
            # Lower bound
            self.bounds[var_name]['LO'] = value
        elif bound_type == "UP":
            # Upper bound
            self.bounds[var_name]['UP'] = value
        elif bound_type == "FX":
            # Fixed value
            self.bounds[var_name]['LO'] = value
            self.bounds[var_name]['UP'] = value
        elif bound_type == "FR":
            # Free variable
            self.bounds[var_name]['LO'] = -float('inf')
            self.bounds[var_name]['UP'] = float('inf')
        elif bound_type == "MI":
            # Minus infinity (lower bound is -inf)
            self.bounds[var_name]['LO'] = -float('inf')
        elif bound_type == "PL":
            # Plus infinity (upper bound is +inf)
            self.bounds[var_name]['UP'] = float('inf')
        elif bound_type == "BV":
            # Binary variable
            self.bounds[var_name]['LO'] = 0.0
            self.bounds[var_name]['UP'] = 1.0
            self.binary_vars.add(var_name)
            self.integer_vars.add(var_name)
        elif bound_type == "LI":
            # Lower bound for integer
            self.bounds[var_name]['LO'] = value
            self.integer_vars.add(var_name)
        elif bound_type == "UI":
            # Upper bound for integer
            self.bounds[var_name]['UP'] = value
            self.integer_vars.add(var_name)
        elif bound_type == "SC":
            raise NotImplementedError("Semi-continuous variables are not supported in this parser.")
        elif bound_type == "SI":
            raise NotImplementedError("Semi-integer variables are not supported in this parser.")

    def _parse_time(self, lines):
        current_section = None
        self.time_mapping = {
            'periods': [],

            # implicit format
            'period_col_start': {},
            'period_row_start': {},

            # Explicit format
            'col_period': {},
            'row_period': {}
        }

        for line in lines:
            line = line.strip()
            if not line or line.startswith('*'):
                continue

            fields = line.split()
            if fields[0] in ["TIME", "PERIODS", "ROWS", "ENDATA"]:
                current_section = fields[0]
                if current_section == "ENDATA":
                    break
                continue

            if current_section == "PERIODS":
                # e.g., COL1  ROW1  PER1
                period_name = fields[2]
                period_col_start = fields[0]
                period_row_start = fields[1]
                self.time_mapping['periods'].append(period_name)
                self.time_mapping['period_col_start'][period_name] = period_col_start
                self.time_mapping['period_row_start'][period_name] = period_row_start

            elif current_section == "ROWS":
                # e.g., ROW1  PER1
                self.time_mapping['row_period'][fields[0]] = fields[1]
            elif current_section == "COLUMNS":
                # e.g., COL1  PER1
                self.time_mapping['col_period'][fields[0]] = fields[1]

        # Transform implicit format to explicit format
        col_current_period = 1
        for col in self.columns:
            if col == self.time_mapping['period_col_start'][self.time_mapping['periods'][1]]:
                col_current_period = 2
            self.time_mapping['col_period'][col] = col_current_period

        row_current_period = 1
        for row in self.rows:
            if row == self.time_mapping['period_row_start'][self.time_mapping['periods'][1]]:
                row_current_period = 2
            self.time_mapping['row_period'][row] = row_current_period

        self.time_mapping = {
            'periods': self.time_mapping['periods'],
            'col_period': self.time_mapping['col_period'],
            'row_period': self.time_mapping['row_period']
        }

    def _parse_sto(self, lines):
        self.scenarios = dict()
        # Can be 'INDEP' or 'SCENARIOS'
        parsing_mode = None
        indep_rv = collections.defaultdict(list)
        current_scenario = None
        current_prob = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('*'):
                continue

            fields = line.split()
            if fields[0] == 'STOCH':
                continue
            if fields[0] == "ENDATA":
                break
            if len(fields) > 1 and fields[0] in ['INDEP', 'SCENARIOS'] and fields[1] == 'DISCRETE':
                parsing_mode = fields[0]
                continue

            if parsing_mode == 'SCENARIOS':
                if fields[0] == 'SC':
                    # New scenario starts
                    scenario_name = fields[1]
                    current_scenario = scenario_name
                    current_prob = float(fields[3])
                    self.scenarios[current_scenario] = {
                        'name': current_scenario,
                        'prob': current_prob,
                        'modi': {'RHS': {}, 'COLUMNS': {}, 'OBJ': {}}
                    }
                elif current_scenario:
                    if fields[0] in ['RIGHT', 'RHS1', 'RHS']:
                        mod_type = 'RHS'
                        name = fields[1]
                        value = float(fields[2])
                        self.scenarios[current_scenario]['modi'][mod_type][name] = value
                    elif fields[1] in ['obj']:
                        mod_type = 'OBJ'
                        name = fields[0]
                        value = float(fields[2])
                        self.scenarios[current_scenario]['modi'][mod_type][name] = value
                    else:
                        raise NotImplementedError(f"Unsupported modification type: {fields}")
                continue

            # INDEP mode
            if parsing_mode == 'INDEP':
                mod_type = fields[0]
                name = fields[1]
                value = float(fields[2])
                prob = float(fields[-1])
                indep_rv[(mod_type, name)].append({'value': value, 'prob': prob})

        if parsing_mode == 'INDEP':
            rv_names = list(indep_rv.keys())
            outcomes = [indep_rv[name] for name in rv_names]

            # For each random variable, prepare a list of outcomes and their probabilities
            choices_map = {}
            for i, rv_name in enumerate(rv_names):
                rv_outcomes = outcomes[i]
                values = [o['value'] for o in rv_outcomes]
                probs = [o['prob'] for o in rv_outcomes]
                choices_map[rv_name] = (values, probs)

            for i in range(self.sample_num):
                scenario_name = f"SCE_{i + 1}"
                modifications = {'RHS': {}, 'COLUMNS': {}, 'OBJ': {}}
                for rv_name, (values, probs) in choices_map.items():
                    # Sample one outcome for each random variable
                    sampled_value = random.choices(values, weights=probs, k=1)[0]
                    mod_type, name = rv_name
                    mod_type = 'RHS' if mod_type in ['RIGHT', 'RHS1'] else mod_type
                    modifications[mod_type][name] = sampled_value

                self.scenarios[scenario_name] = {
                    'name': scenario_name,
                    'prob': 1.0 / self.sample_num,
                    'modi': modifications
                }

    def to_json(self, file_path):
        data = {
            'model_name': self.model_name,
            'objective_sense': self.objective_sense,
            'objective_name': self.objective_name,
            'rows': self.rows,
            'columns': self.columns,
            'rhs': self.rhs,
            'bounds': self.bounds,
            'integer_vars': list(self.integer_vars),
            'binary_vars': list(self.binary_vars),
            'time_mapping': self.time_mapping,
            'scenarios': self.scenarios,
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)


# %%
# Define the first-stage problem.

def first_stage_model(data, enforce_integer=False):
    # --- Get stage variables ---
    stage1_vars = [col for col, per in data['time_mapping']['col_period'].items() if per == 1]

    model = gp.Model(data['model_name'])

    # First-stage variables
    x = {}
    for var_name in stage1_vars:
        bounds = data['bounds'].get(var_name, {})
        lb = bounds.get('LO', 0.0)
        ub = bounds.get('UP', float('inf'))

        if enforce_integer:
            vtype = GRB.INTEGER
        else:
            vtype = GRB.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = GRB.INTEGER
            if var_name in data['binary_vars']:
                vtype = GRB.BINARY

        if abs(lb) < float('inf') and abs(ub) < float('inf'):
            if int(lb) == 0 and int(ub) == 1 and vtype == GRB.INTEGER:
                vtype = GRB.BINARY

        x[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=var_name)

    # reate constraints
    for row_name, row_type in data['rows'].items():
        if row_type == 'N':
            # Objective row
            continue

        row_period = data['time_mapping']['row_period'].get(row_name)

        if row_period == 1:
            # First-stage constraints
            expr = gp.LinExpr()
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
    obj_expr = gp.LinExpr()
    obj_row_name = data['objective_name']

    # First-stage cost
    for col_name, coeff in data['columns'].items():
        if obj_row_name in coeff and col_name in x:
            obj_expr += coeff[obj_row_name] * x[col_name]

    model.setObjective(obj_expr, sense=GRB.MINIMIZE if data['objective_sense'] == 'MIN' else GRB.MAXIMIZE)

    return model, stage1_vars


# %%
# Define the second-stage problems for each scenario.

def second_stage_model(data):
    stage1_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 1}
    stage2_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 2}

    models = []
    probs = []
    for scenario_name, s_data in data['scenarios'].items():
        probs.append(s_data['prob'])
        model = gp.Model(f"{data['model_name']}_{scenario_name}")

        # First-stage variables (as continuous)
        x = {}
        for var_name in stage1_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = bounds.get('LO', 0.0)
            ub = bounds.get('UP', float('inf'))
            x[var_name] = model.addVar(lb=lb, ub=ub, vtype=GRB.CONTINUOUS, name=var_name)

        # Second-stage variables
        y = {}
        for var_name in stage2_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = bounds.get('LO', 0.0)
            ub = bounds.get('UP', float('inf'))
            vtype = GRB.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = GRB.INTEGER
            if var_name in data['binary_vars']:
                vtype = GRB.BINARY
            y[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=f"{var_name}_{scenario_name}")

        # Create constraints
        for row_name, row_type in data['rows'].items():
            if row_type == 'N':
                continue

            row_period = data['time_mapping']['row_period'].get(row_name)

            if row_period == 2:
                expr = gp.LinExpr()
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
        obj_expr = gp.LinExpr()
        obj_row_name = data['objective_name']
        obj_modifications = s_data['modi'].get('OBJ', {})

        # Second-stage cost
        for col_name, coeff in data['columns'].items():
            if obj_row_name in coeff and col_name in y:
                # Use modified coefficient if available, otherwise use original
                obj_coeff = obj_modifications.get(col_name, coeff[obj_row_name])
                obj_expr += obj_coeff * y[col_name]

        model.setObjective(obj_expr, sense=GRB.MINIMIZE if data['objective_sense'] == 'MIN' else GRB.MAXIMIZE)
        models.append(model)

    return models, probs


# %%
# Define the deterministic equivalent model that combines all scenarios into a single large model.

def deterministic_equivalent_model(data, enforce_integer=False):
    stage1_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 1}
    stage2_vars = {col for col, per in data['time_mapping']['col_period'].items() if per == 2}

    model = gp.Model(data['model_name'])

    # First-stage variables
    x = {}
    for var_name in stage1_vars:
        bounds = data['bounds'].get(var_name, {})
        lb = bounds.get('LO', 0.0)
        ub = bounds.get('UP', float('inf'))

        if enforce_integer:
            vtype = GRB.INTEGER
        else:
            vtype = GRB.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = GRB.INTEGER
            if var_name in data['binary_vars']:
                vtype = GRB.BINARY

        if abs(lb) < float('inf') and abs(ub) < float('inf'):
            if int(lb) == 0 and int(ub) == 1 and vtype == GRB.INTEGER:
                vtype = GRB.BINARY

        x[var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=var_name)

    # Second-stage variables
    y = {}
    scenarios = data['scenarios']
    for s_name in scenarios:
        y[s_name] = {}
        for var_name in stage2_vars:
            bounds = data['bounds'].get(var_name, {})
            lb = bounds.get('LO', 0.0)
            ub = bounds.get('UP', float('inf'))
            vtype = GRB.CONTINUOUS
            if var_name in data['integer_vars']:
                vtype = GRB.INTEGER
            if var_name in data['binary_vars']:
                vtype = GRB.BINARY
            y[s_name][var_name] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=f"{var_name}_{s_name}")

    # Create constraints
    for row_name, row_type in data['rows'].items():
        if row_type == 'N':
            # Objective row
            continue

        row_period = data['time_mapping']['row_period'].get(row_name)

        if row_period == 1:
            # First-stage constraints
            expr = gp.LinExpr()
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
                expr = gp.LinExpr()
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
    obj_expr = gp.LinExpr()
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

    model.setObjective(obj_expr, sense=GRB.MINIMIZE if data['objective_sense'] == 'MIN' else GRB.MAXIMIZE)

    return model


# %%
# Set memory limit for solution methods.


def limit_memory(limit_gb: float):
    import resource
    import sys
    from functools import wraps

    def decorator(func):
        if sys.platform == "win32":
            @wraps(func)
            def windows_wrapper(*args, **kwargs):
                print(f"Warning: Memory limit of {limit_gb} GB not applied "
                      f"(resource module is not available on Windows).")
                return func(*args, **kwargs)

            return windows_wrapper

        @wraps(func)
        def unix_wrapper(*args, **kwargs):
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)

            limit_bytes = int(limit_gb * 1024 * 1024 * 1024)

            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))
                print(f"INFO: Memory limit for '{func.__name__}' set to {limit_gb} GB.")

            except:
                print(f"Error: Failed to set memory limit for function '{func.__name__}'.")

            try:
                result = func(*args, **kwargs)
                return result

            except:
                print(f"Error: Out-of-Memory in function '{func.__name__}'.")
                return None

            finally:
                resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
                print(f"INFO: Memory limit for '{func.__name__}' restored to original value.")

        return unix_wrapper

    return decorator


# %%
# Compare computation time of different solution methods.

def collect_data(ins_names, de_files, bd_files, ins_classes, sample_nums):
    data_points = []

    for ins_name, de_file, bd_file, ins_class, num in zip(ins_names, de_files, bd_files, ins_classes, sample_nums):
        time_de, time_bd = 3600, 3600
        de_solved, bd_solved = False, False

        try:
            with open(de_file, 'r') as f:
                result = json.load(f)
                time_de = result['SolutionInfo']['Runtime']
                if result['SolutionInfo']['MIPGap'] <= 1e-4:
                    de_solved = True
        except FileNotFoundError:
            print(f"Warning: Data for < {de_file} > not found.")

        try:
            with open(bd_file, 'r') as f:
                result = json.load(f)
                time_bd = result['runtime']
                if result.get('gap', float('inf')) <= 1e-4:
                    bd_solved = True
        except FileNotFoundError:
            print(f"Warning: Data for < {bd_file} > not found.")

        data_points.append({
            'instance_name': ins_name,
            'instance_class': ins_class,
            'sample_num': num,
            'time_de': time_de,
            'time_bd': time_bd,
            'de_solved': de_solved,
            'bd_solved': bd_solved,
        })

    return data_points


def draw(all_data_points, titles=None):
    ...
