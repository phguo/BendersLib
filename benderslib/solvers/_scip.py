# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from pyscipopt import Model, Expr, SCIP_PARAMSETTING, Conshdlr, SCIP_RESULT, SCIP_PROPTIMING, SCIP_PRESOLTIMING

from ..consts import BendersConsts as CST
from ._base import SolverBase
from ..errors import BendersNotImplementedError, MismatchedProbabilityError, BendersBackendError


class _ScipConshdlr(Conshdlr):

    def __init__(self, solver_instance):
        super().__init__()
        self.solver = solver_instance

    def conscheck(self, constraints, solution, check_integrality, check_lp_rows, print_reason, completely, **results):
        return {"result": SCIP_RESULT.INFEASIBLE}

    def consenfolp(self, constraints, n_useful_conss, sol_infeasible):
        self.solver._callback_where = CST.INCUMBENT

        # SCIP may call this with sol=None, which means the current LP solution.
        # We are only interested in integer feasible solutions.
        # getBestSol() gives us the best integer solution found so far.

        # sol = self.model.getBestSol()
        # if sol is None:
        #     return {"result": SCIP_RESULT.DIDNOTRUN}

        benders_result = self.solver._callback_handler(self.solver)

        if benders_result == CST.TERMINATE:
            self.model.interruptSolve()
            return {"result": SCIP_RESULT.FEASIBLE}

        return {"result": SCIP_RESULT.INFEASIBLE}

    def conslock(self, constraint, locktype, nlockspos, nlocksneg):
        # Lock all master problem variables.
        # DOC: https://www.scipopt.org/doc/html/CONS.php
        for var in self.solver._vars_map.values():
            self.model.addVarLocks(var, nlockspos + nlocksneg, nlockspos + nlocksneg)


class Scip(SolverBase):
    """SCIP solver interface for BendersLib.

    This class provides an interface to the SCIP solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: pyscipopt.Model
        An instance of SCIP's ``pyscipopt.Model``.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    __SCIP_VAR_UB = 1e20
    """Default upper bound for SCIP variables."""
    __SCIP_INVALID = 1e99
    """A large number that SCIP uses to indicate invalid duals or extreme rays."""

    def __init__(self, model: Model, solver_options: dict = None) -> None:
        super().__init__(model)

        # Supporting method like getVarByName and getConsByName
        self._vars_map = {v.name: v for v in self.model.getVars(transformed=False)}
        self._cons_map = {c.name: c for c in self.model.getConss(transformed=False)}

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        self._callback_where = None

        self._sense = CST.MIN if self.model.getObjectiveSense() == 'minimize' else CST.MAX
        self._all_vars = list(self._vars_map.keys())
        self._bin_vars = [var_name for var_name, var in self._vars_map.items() if var.vtype() == 'BINARY']
        self._int_vars = [var_name for var_name, var in self._vars_map.items() if var.vtype() == 'INTEGER']

        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            var_name: (var.getLbGlobal(), var.getUbGlobal())
            for var_name, var in self._vars_map.items()
            if var.getLbGlobal() != 0 or var.getUbGlobal() < self.__SCIP_VAR_UB}

        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.getConss(transformed=False))

        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        if self.model.getObjectiveSense() == 'maximize':
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        # Workaround to fix wrong dual values when bound constraints are present
        # https://pyscipopt.readthedocs.io/en/latest/tutorials/constypes.html#id4
        # https://stackoverflow.com/questions/79463159/unable-to-get-dual-values-from-scip-solver

        # If there are variable bounds
        # if self._var_bounds:
        #     raise BendersBackendError(
        #         "BendersLib currently does not support variable bounds in SCIP, due to a SCIP limitation.")

        # If there are bound constraints
        # for cons in self.model.getConss(transformed=False):
        #     if len(self.model.getConsVars(cons)) == 1:
        #         raise BendersBackendError(
        #             "BendersLib currently does not support bound constraints in SCIP, due to a SCIP limitation.")

        # Define variable bounds as constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self._vars_map[var_name]
            if lb > 0:
                self._cons_map[f"__{var_name}_lb"] = self.model.addCons(var >= lb, name=f"__{var_name}_lb")
            if ub < self.__SCIP_VAR_UB:
                self._cons_map[f"__{var_name}_ub"] = self.model.addCons(var <= ub, name=f"__{var_name}_ub")

    def __setup_model(self, solver_options: dict = None):
        # Hide output
        self.model.hideOutput()
        # Turn off presolve to get correct dual values
        self.model.setPresolve(SCIP_PARAMSETTING.OFF)
        self.model.setHeuristics(SCIP_PARAMSETTING.OFF)
        self.model.disablePropagation()

        _options = self._options['SCIP_OPTIONS']
        # Prioritize user options
        solver_options = solver_options or {}
        _options.update(solver_options)

        self.model.setParams(_options)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1.0]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise MismatchedProbabilityError("Length of <prob> must match length of <estimators>.")

        for name, obj in zip(estimators, prob):
            self._vars_map[name] = self.model.addVar(name=name, vtype='C', lb=lb, obj=obj)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        self.model.freeTransform()
        for var_name, value in var_values.items():
            var = self._vars_map[var_name]
            self.model.chgVarLb(var, value)
            self.model.chgVarUb(var, value)
            # self.model.fixVar(var, value)

    def unfix_vars(self, vars: list[str]) -> None:
        self.model.freeTransform()
        for var_name in vars:
            var = self._vars_map[var_name]
            lb, ub = self._var_bounds.get(var_name, (0, self.__SCIP_VAR_UB))
            self.model.chgVarLb(var, lb)
            self.model.chgVarUb(var, ub)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        all_var_values = self.model.getVarDict()
        if vars is not None:
            return {var_name: all_var_values[var_name] for var_name in vars}
        return all_var_values

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        result = {vars: [] for vars in (vars or self._all_vars)}

        for cons in self._cons_map.values():
            var_coefs = self.model.getValsLinear(cons)
            for var_name in result.keys():
                coef = var_coefs.get(var_name, 0.0)
                result[var_name].append(coef)

        return result

    def get_rhs(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        lhs = [self.model.getLhs(c) for c in cons]
        rhs = [self.model.getRhs(c) for c in cons]

        res = []
        self._sense = []
        for l, r in zip(lhs, rhs):
            if l <= -self.__SCIP_VAR_UB:
                res.append(r)
                self._sense.append('<=')
            elif r >= self.__SCIP_VAR_UB:
                res.append(l)
                self._sense.append('>=')

        return res

    def get_dual_values(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        duals = [self.model.getDualSolVal(c) for c in cons]

        if self.__SCIP_INVALID in duals:
            raise BendersBackendError("SCIP returned an invalid dual value with 1e+99.")

        return duals

    def get_extreme_ray(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        ray = [self.model.getDualfarkasLinear(c) for c in cons]

        if self.__SCIP_INVALID in ray:
            raise BendersBackendError("SCIP returned an invalid extreme ray with 1e+99.")

        # SCIP returns Farkas Dual with opposite sign to Gurobi
        ray = [-r for r in ray]
        return ray

    def get_obj(self) -> float:
        obj = self.model.getObjVal()
        return obj

    def add_cut(self, cut, name=None) -> None:
        lhs = sum(coef * self._vars_map[var] for var, coef in zip(cut.vars, cut.coefs))

        # Cut cannot be added in the "problem solved stage"
        self.model.freeTransform()

        if cut.sense == CST.EQ:
            self._cons_map[name] = self.model.addCons(lhs == cut.rhs, name=name)
        elif cut.sense == CST.LE:
            self._cons_map[name] = self.model.addCons(lhs <= cut.rhs, name=name)
        elif cut.sense == CST.GE:
            self._cons_map[name] = self.model.addCons(lhs >= cut.rhs, name=name)

    def remove_cut(self, cut_name: str) -> None:
        self.model.freeTransform()

        cons = self._cons_map[cut_name]
        self.model.delCons(cons)
        self._cons_map.pop(cut_name)

    def solve(self) -> None:
        # self.model.freeTransform()
        self.model.optimize()
        self._update_status('SCIP', self.model.getStatus().lower())

    def _bnc_solve(self, callback_handler) -> None:
        # Callback
        self._callback_handler = callback_handler

        # Constraint handler
        # https://github.com/scipopt/PySCIPOpt/blob/master/examples/finished/lotsizing_lazy.py
        # https://github.com/scipopt/PySCIPOpt/blob/master/examples/unfinished/tsp_lazy.py
        conshdlr = _ScipConshdlr(self)
        self.model.includeConshdlr(
            conshdlr, "BendersCut", "Constraint handler for Benders cuts",
            sepapriority=0, enfopriority=-1, chckpriority=-1, sepafreq=-1, propfreq=-1,
            eagerfreq=-1, maxprerounds=0, delaysepa=False, delayprop=False, needscons=False,
            presoltiming=SCIP_PRESOLTIMING.FAST, proptiming=SCIP_PROPTIMING.BEFORELP
        )

        # Solve
        self.model.optimize()
        self._update_status('SCIP', self.model.getStatus().lower())

    def _cb_get_obj(self):
        obj = self.model.getObjVal()
        return obj

    def _cb_get_bound(self):
        lb = self.model.getLowerbound()
        return lb

    def _cb_get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        sol = self.model.getBestSol()

        return {var: self.model.getSolVal(sol, self._vars_map[var]) for var in vars_to_get}

    def _cb_add_cut(self, cut) -> None:

        lhs = sum(coef * self._vars_map[var] for var, coef in zip(cut.vars, cut.coefs))

        if cut.sense == CST.EQ:
            self.model.addCons(lhs == cut.rhs)
        elif cut.sense == CST.LE:
            self.model.addCons(lhs <= cut.rhs)
        elif cut.sense == CST.GE:
            self.model.addCons(lhs >= cut.rhs)

    def compute_iis(self) -> set[str]:
        self.model.hideOutput()
        iis = self.model.generateIIS()
        iis_scip = iis.getSubscip()

        vars = set()

        # Constraints
        for cons in iis_scip.getConss():
            for var in self.model.getConsVars(cons):
                vars.add(var.name)

        # Variables
        for var in iis_scip.getVars():
            vars.add(var.name)

        return vars

    @staticmethod
    def make_master_problem(original_model: Model, master_vars: list[str]) -> Model:
        master = Model(sourceModel=original_model)

        # Remove non-master variables & remove them from objective (will be handled automatically)
        vars = master.getVars(transformed=False)
        _vars_to_del_idx = []

        for i, var in enumerate(vars):
            if var.name not in master_vars:
                _vars_to_del_idx.append(i)

        # Remove constraints that contains non-master variables
        _cons_to_remove_idx = []
        constrs = master.getConss(transformed=False)

        for i, cons in enumerate(constrs):
            for var in master.getConsVars(cons):
                if var.name not in master_vars:
                    _cons_to_remove_idx.append(i)
                    break

        # Execute removal
        for i in reversed(_vars_to_del_idx):
            master.delVar(vars[i])

        for i in reversed(_cons_to_remove_idx):
            master.delCons(constrs[i])

        return master

    @staticmethod
    def make_sub_problem(original_model: Model, master_vars: list[str]) -> Model:
        sub = Model(sourceModel=original_model)

        # Set master variables to continuous & remove them from objective
        obj = sub.getObjective()
        new_obj = Expr()
        for var in sub.getVars(transformed=False):
            if var.name in master_vars:
                sub.chgVarType(var, 'C')
            else:
                new_obj += obj[var] * var
        sub.setObjective(new_obj, 'minimize')

        # Remove constraints that contains only master variables
        _cons_to_remove_idx = []
        constrs = sub.getConss(transformed=False)

        for i, cons in enumerate(constrs):
            is_master_only = True
            for var in sub.getConsVars(cons):
                if var.name not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_remove_idx.append(i)

        # Execute removal
        for i in reversed(_cons_to_remove_idx):
            sub.delCons(constrs[i])

        return sub
