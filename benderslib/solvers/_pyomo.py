# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import io
import logging

import pyomo.environ as pyo
from pyomo.core import Var, Objective, Constraint
from pyomo.core.expr.visitor import identify_variables
from pyomo.repn import generate_standard_repn
from pyomo.contrib.iis.mis import compute_infeasibility_explanation as mis

from ..consts import BendersConsts as CST
from ._base import SolverBase
from ..errors import BendersNotImplementedError, MismatchedProbabilityError, BendersBackendError


class Pyomo(SolverBase):
    """Pyomo solver interface for BendersLib.

    This class provides an interface to Pyomo for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------

    model: pyomo.environ.ConcreteModel
        An instance of Pyomo's ``ConcreteModel``.
    solver: str
        The solver to be used with Pyomo (e.g., ``'gurobi'``, ``'gurobi_direct'``, etc.,
        see :ref:`supported solvers <solver-table>`).
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: pyo.ConcreteModel, solver: str, solver_options: dict = None) -> None:
        super().__init__(model)

        self.__solver_name = solver.lower()
        self.__is_persistent = self.__solver_name.endswith('_persistent')
        self.__solver_options = solver_options if solver_options is not None else {}
        self.solver_factory = self.__init_solver_factory()

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        objectives = list(model.component_data_objects(Objective, active=True))
        if len(objectives) != 1:
            raise BendersBackendError("Pyomo models must have exactly one active objective.")
        self._sense = CST.MIN if objectives[0].sense == pyo.minimize else CST.MAX
        self._all_vars = [v.name for v in model.component_data_objects(Var)]
        self._bin_vars = [v.name for v in model.component_data_objects(Var) if v.is_binary()]
        self._int_vars = [v.name for v in model.component_data_objects(Var) if v.is_integer() and not v.is_binary()]

        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {}
        for v in model.component_data_objects(Var):
            lb = v.lb if v.lb is not None else -float('inf')
            ub = v.ub if v.ub is not None else float('inf')
            if lb != 0 or ub != float('inf'):
                self._var_bounds[v.name] = (lb, ub)

        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(list(model.component_data_objects(Constraint, active=True)))

        # If the model has no integer and binary variables, we can access dual values
        if len(self._bin_vars) + len(self._int_vars) == 0:
            if not hasattr(self.model, 'dual'):
                self.model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

        # Persistent solvers
        if self.__is_persistent:
            self.solver_factory.set_instance(self.model)

    def __init_solver_factory(self) -> pyo.SolverFactory:
        _options = self._options['PYOMO_OPTIONS'].get(self.__solver_name, {})

        # Prioritize user options
        _options.update(self.__solver_options)

        solver_factory = pyo.SolverFactory(self.__solver_name, options=_options)
        return solver_factory

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self._sense == CST.MAX:
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            # From here, the default variable bounds become (0, +inf), despite that the Pyomo default is (-inf, +inf).
            raise BendersNotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.find_component(var_name)
            if lb > 0:
                self.model.add_component(f"_{var_name}_lb", Constraint(expr=var >= lb))
                var.setlb(0)
            if ub < float('inf'):
                self.model.add_component(f"_{var_name}_ub", Constraint(expr=var <= ub))
                var.setub(None)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1]
            else:
                prob = [1 / len(estimators)] * len(estimators)

        if len(prob) != len(estimators):
            raise MismatchedProbabilityError("Length of <prob> must match length of <estimators>.")

        obj = next(self.model.component_data_objects(Objective, active=True))

        for name, p in zip(estimators, prob):
            var = Var(within=pyo.Reals, bounds=(lb, None))
            self.model.add_component(name, var)
            obj.expr += p * self.model.find_component(name)

            # Persistent solvers
            if self.__is_persistent:
                self.solver_factory.add_var(var)

        # Persistent solvers
        if self.__is_persistent:
            self.solver_factory.set_objective(obj)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self.model.find_component(var_name)
            var.fix(var_value)

            # Persistent solvers
            if self.__is_persistent:
                self.solver_factory.update_var(var)

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            var = self.model.find_component(var_name)
            # var.set_value(None)
            var.unfix()

            # Persistent solvers
            if self.__is_persistent:
                self.solver_factory.update_var(var)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: pyo.value(self.model.find_component(var_name)) for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        vars_to_get = vars or self._all_vars
        coefs = {v: [] for v in vars_to_get}

        cons = self.model.component_data_objects(Constraint, active=True)
        for c in cons:
            repn = generate_standard_repn(c.body)
            coef_dict = {var.name: coef for var, coef in zip(repn.linear_vars, repn.linear_coefs)}
            for v in vars_to_get:
                coefs[v].append(coef_dict.get(v, 0.0))

        return coefs

    def get_rhs(self) -> list[float]:
        cons = self.model.component_data_objects(Constraint, active=True)
        rhs = []
        for c in cons:
            if c.equality or (c.has_lb() and not c.has_ub()):
                bound = c.lower
            elif c.has_ub() and not c.has_lb():
                bound = c.upper
            else:
                raise BendersBackendError(f"Constraint has both bounds ({c.lower}, {c.upper}). Cannot determine RHS.")
            rhs.append(pyo.value(bound) - generate_standard_repn(c.body).constant)
        return rhs

    def get_dual_values(self) -> list[float]:
        if self.__solver_name == 'scip':
            raise BendersBackendError("BendersLib cannot get correct dual values with Pyomo(solver='scip').")

        constraints = self.model.component_data_objects(pyo.Constraint, active=True)
        duals = [self.model.dual[c] for c in constraints]
        return duals

    def get_extreme_ray(self) -> list[float]:
        if self.__solver_name == 'gurobi_persistent':
            constraints = self.model.component_data_objects(pyo.Constraint, active=True)
            ray = [self.solver_factory.get_linear_constraint_attr(c, 'FarkasDual') for c in constraints]
        else:
            raise BendersBackendError(
                "Farkas dual (for feasibility cuts) is only supported by the 'gurobi_persistent' solver in Pyomo.")

        return ray

    def get_obj(self) -> float:
        obj = next(self.model.component_data_objects(Objective, active=True))
        return pyo.value(obj.expr)

    def add_cut(self, cut, name=None) -> None:
        vars = [self.model.find_component(v) for v in cut.vars]
        expr = sum(coef * var for coef, var in zip(cut.coefs, vars))

        if cut.sense == CST.EQ:
            cons = Constraint(expr=expr == cut.rhs)
            self.model.add_component(name, cons)
        elif cut.sense == CST.LE:
            cons = Constraint(expr=expr <= cut.rhs)
            self.model.add_component(name, cons)
        elif cut.sense == CST.GE:
            cons = Constraint(expr=expr >= cut.rhs)
            self.model.add_component(name, cons)

        # Persistent solvers
        if self.__is_persistent:
            self.solver_factory.add_constraint(cons)

    def remove_cut(self, cut_name: str) -> None:
        if self.__is_persistent:
            self.solver_factory.remove_constraint(self.model.find_component(cut_name))
        self.model.del_component(cut_name)

    def solve(self) -> None:
        results = self.solver_factory.solve(self.model, tee=False, load_solutions=False)
        self._update_status('PYOMO', results.solver.termination_condition)

        if self.status == CST.OPTIMAL:
            # Load solution back to the model
            self.model.solutions.load_from(results)

    def compute_iis(self):
        log_stream = io.StringIO()

        logging.getLogger('pyomo').setLevel(logging.ERROR)
        logger = logging.getLogger('pyomo.contrib.iis')
        logger.propagate = False

        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(log_stream)
        logger.addHandler(handler)

        _solver = pyo.SolverFactory(self.__solver_name, load_solutions=False)
        mis(self.model, solver=_solver, logger=logger)
        logger.removeHandler(handler)
        logger.propagate = True

        output = log_stream.getvalue()

        return self.__get_mis_vars(output)

    def __get_mis_vars(self, mis_output: str):
        mis_cons = []
        mis_vars = set()

        in_mis_section = False
        for line in mis_output.splitlines():
            line = line.strip()
            if not line:
                continue

            if "Computed Minimal Intractable System (MIS)!" in line:
                in_mis_section = True
                continue

            if in_mis_section:
                parts = line.split('\t')
                for part in parts:
                    part = part.strip()
                    if part.startswith("constraint:"):
                        mis_cons.append(part.replace("constraint:", "").strip())
                    elif part.startswith("ub of var") or part.startswith("lb of var"):
                        mis_vars.add(part.split()[-1])

        for c_name in mis_cons:
            constraint = getattr(self.model, c_name)
            for var in identify_variables(constraint.expr):
                mis_vars.add(var.name)

        return mis_vars

    @staticmethod
    def make_master_problem(original_model: pyo.ConcreteModel, master_vars: list[str]) -> pyo.ConcreteModel:
        master = original_model.clone()

        # Remove non-master variables from objective (ONLY handle linear case)
        obj = next(master.component_data_objects(Objective, active=True))
        repn = generate_standard_repn(obj.expr)
        new_expr = sum(
            coef * master.find_component(var.name)
            for coef, var in zip(repn.linear_coefs, repn.linear_vars)
            if var.name in master_vars
        )
        master.del_component(obj)
        master.obj = Objective(expr=new_expr + repn.constant, sense=pyo.minimize)

        # Remove constraints that contains non-master variables
        _cons_to_remove_idx = []
        constrs = list(master.component_data_objects(Constraint, active=True))

        for i, constr in enumerate(constrs):
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    _cons_to_remove_idx.append(i)
                    break

        # Execute removal
        for i in reversed(_cons_to_remove_idx):
            # constrs[i].deactivate()
            cons = constrs[i]
            del cons.parent_component()[cons.index()]

        # Remove non-master variables
        _vars_to_remove_idx = []
        vars = list(master.component_data_objects(Var, active=True))

        for i, var in enumerate(vars):
            if var.name not in master_vars:
                _vars_to_remove_idx.append(i)

        # Execute removal
        for i in reversed(_vars_to_remove_idx):
            var = vars[i]
            del var.parent_component()[var.index()]

        return master

    @staticmethod
    def make_sub_problem(original_model: pyo.ConcreteModel, master_vars: list[str]) -> pyo.ConcreteModel:
        sub = original_model.clone()

        # Set master variables to continuous
        for var_name in master_vars:
            var = sub.find_component(var_name)
            # Set potentially binary/integer master variables to continuous for obtaining duals
            var.domain = pyo.Reals

        # Remove master variables from objective (ONLY handle linear case)
        obj = next(sub.component_data_objects(Objective, active=True))
        repn = generate_standard_repn(obj.expr)
        new_expr = sum(
            coef * var
            for coef, var in zip(repn.linear_coefs, repn.linear_vars)
            if var.name not in master_vars
        )
        sub.del_component(obj)
        sub.obj = Objective(expr=new_expr, sense=pyo.minimize)

        # Remove constraints that contains only master variables
        _cons_to_remove_idx = []
        constrs = list(sub.component_data_objects(Constraint, active=True))

        for i, constr in enumerate(constrs):
            is_master_only = True
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_remove_idx.append(i)

        # Execute removal
        for i in reversed(_cons_to_remove_idx):
            # constrs[i].deactivate()
            cons = constrs[i]
            del cons.parent_component()[cons.index()]

        return sub
