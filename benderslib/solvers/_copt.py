# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from coptpy import Model, LinExpr, COPT, CallbackBase

from ..consts import BendersConsts as CST
from ._base import SolverBase
from ..errors import BendersNotImplementedError, MismatchedProbabilityError, BendersCallbackError, BendersBackendError


class _CoptCallback(CallbackBase):
    def __init__(self, solver_instance):
        super().__init__()
        self.solver = solver_instance

    def callback(self):
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            self.solver._callback_where = CST.INCUMBENT

            r = self.solver._callback_handler(self.solver)

            if r == CST.TERMINATE:
                self.interrupt()

        if self.where() == COPT.CBCONTEXT_MIPNODE and self.solver.params.bnc_frac_sol:
            self.solver._callback_where = CST.NODE

            r = self.solver._callback_handler(self.solver)

            if r == CST.TERMINATE:
                self.interrupt()


class Copt(SolverBase):
    """COPT solver interface for BendersLib.

    This class provides an interface to the COPT solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: coptpy.Model
        An instance of COPT's ``coptpy.Model``.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: Model, solver_options: dict = None) -> None:
        super().__init__(model)

        # Attributes in COPT Model
        sense = model.objsense
        variables = model.getVars()
        vtypes = [v.getType() for v in variables]
        lbs = [v.getInfo(COPT.Info.LB) for v in variables]
        ubs = [v.getInfo(COPT.Info.UB) for v in variables]

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        self._sense = CST.MIN if sense == COPT.MINIMIZE else CST.MAX
        self._all_vars = [v.getName() for v in variables]
        self._bin_vars = [v for v, t in zip(self._all_vars, vtypes) if t == COPT.BINARY]
        self._int_vars = [v for v, t in zip(self._all_vars, vtypes) if t == COPT.INTEGER]
        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if lb != 0 or ub != COPT.INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.getConstrs())

        self.__setup_model(solver_options)

        # For BnC callback
        self._callback_handler = None
        self._callback_where = None

    def __standardize(self):
        self.__check_objective_sense(self.model)
        self.__bounds_to_constrs()

    @staticmethod
    def __check_objective_sense(model):
        if model.objsense == COPT.MAXIMIZE:
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise BendersNotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.getVarByName(var_name)
            if lb != 0:
                self.model.addConstr(var >= lb)
                var.lb = 0
            if ub < COPT.INFINITY:
                self.model.addConstr(var <= ub)
                var.ub = COPT.INFINITY

    def __setup_model(self, solver_options: dict = None):
        _options = self._options['COPT_OPTIONS']

        # Prioritize user options
        solver_options = solver_options or {}
        _options.update(solver_options)

        for option, value in _options.items():
            self.model.setParam(option, value)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise MismatchedProbabilityError("Length of <prob> must match length of <estimators>.")

        for var_name, obj in zip(estimators, prob):
            self.model.addVar(lb=lb, vtype=COPT.CONTINUOUS, obj=obj, name=var_name)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self.model.getVarByName(var_name)
            var.lb = var_value
            var.ub = var_value

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            var = self.model.getVarByName(var_name)
            var.lb, var.ub = self._var_bounds.get(var_name, (0, COPT.INFINITY))

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: self.model.getVarByName(var_name).x for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        res = {}
        _vars = vars or self._all_vars

        for v in _vars:
            var = self.model.getVarByName(v)
            coefs = [self.model.getCoeff(cons, var) for cons in self.model.getConstrs()]
            res[v] = coefs
        return res

    def get_rhs(self) -> list[float]:
        cons = self.model.getConstrs()
        rhs = []
        for c in cons:
            if c.ub == COPT.INFINITY:
                rhs.append(c.lb)
            elif c.lb == -COPT.INFINITY:
                rhs.append(c.ub)
            elif c.lb == c.ub:
                rhs.append(c.lb)
            else:
                raise BendersBackendError(f"Constraint has both bounds ({c.lb}, {c.ub}). Cannot determine RHS.")
        return rhs

    def get_dual_values(self) -> list[float]:
        # ONLY available for LP problems
        return self.model.getDuals()

    def get_extreme_ray(self) -> list[float]:
        has_nl_cons = not self.model.getAttr("Rows") == len(self.model.getConstrs())

        if has_nl_cons:
            raise BendersBackendError("Unable to obtain FarkasDual from COPT model with nonlinear constraints.")

        else:
            has_nl_obj = (
                    self.model.getAttr("HasQObj")
                    or self.model.getAttr("HasNLObj")
                    or self.model.getAttr("HasPSDObj")
            )

            if has_nl_obj:
                _m = self.model.clone()
                _m.setObjective(0, sense=COPT.MINIMIZE)
                _m.solve()
                ray = _m.getInfo(COPT.Info.DualFarkas, _m.getConstrs())
            else:
                ray = self.model.getInfo(COPT.Info.DualFarkas, self.model.getConstrs())

            # COPT returns Farkas Dual with opposite sign to Gurobi
            ray = [-r for r in ray]
            return ray

    def get_obj(self) -> float:
        return self.model.objval

    def add_cut(self, cut, name=None) -> None:
        lhs = LinExpr()
        for var, coef in zip(cut.vars, cut.coefs):
            lhs.addTerm(self.model.getVarByName(var), coef)

        _sense_map = {
            CST.EQ: COPT.EQUAL,
            CST.LE: COPT.LESS_EQUAL,
            CST.GE: COPT.GREATER_EQUAL
        }

        self.model.addConstr(lhs, sense=_sense_map[cut.sense], rhs=cut.rhs, name=name)

    def remove_cut(self, cut_name: str) -> None:
        con = self.model.getConstrByName(cut_name)
        self.model.remove(con)

    def solve(self) -> None:
        # COPT 8.0.4 can retain infeasibility after variable bounds change.
        if self.status == CST.INFEASIBLE:
            self.model.reset()
        self.model.solve()
        self._update_status('COPT', self.model.status)

    def _bnc_solve(self, callback_handler) -> None:
        self.model.setParam('LazyConstraints', 1)

        # Callback
        self._callback_handler = callback_handler
        self.__copt_cb = _CoptCallback(self)
        self.model.setCallback(self.__copt_cb, COPT.CBCONTEXT_MIPSOL | COPT.CBCONTEXT_MIPNODE)

        # Solve
        self.model.solve()
        self._update_status('COPT', self.model.status)

    def _cb_get_obj(self):
        if self._callback_where == CST.INCUMBENT:
            obj = self.__copt_cb.getInfo(COPT.cbinfo.MipCandObj)

        elif self._callback_where == CST.NODE:
            obj = self.__copt_cb.getInfo(COPT.cbinfo.RelaxSolObj)

        else:
            raise BendersCallbackError("Invalid callback where. Expected 'INCUMBENT' or 'NODE'.")

        return obj

    def _cb_get_bound(self):
        bound = self.__copt_cb.getInfo(COPT.cbinfo.BestBnd)

        return bound if bound > -COPT.INFINITY else float('-inf')

    def _cb_get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars = vars or [v.getName() for v in self.model.getVars()]

        if self._callback_where == CST.INCUMBENT:
            vals = {n: self.__copt_cb.getSolution(self.model.getVarByName(n)) for n in vars}
        elif self._callback_where == CST.NODE:
            vals = {n: self.__copt_cb.getRelaxSol(self.model.getVarByName(n)) for n in vars}
        else:
            raise BendersCallbackError("Invalid callback where. Expected 'INCUMBENT' or 'NODE'.")

        return vals

    def _cb_add_cut(self, cut) -> None:
        lhs = LinExpr()
        for var, coef in zip(cut.vars, cut.coefs):
            lhs.addTerm(self.model.getVarByName(var), coef)

        _sense_map = {
            CST.EQ: COPT.EQUAL,
            CST.LE: COPT.LESS_EQUAL,
            CST.GE: COPT.GREATER_EQUAL
        }

        self.__copt_cb.addLazyConstr(lhs, sense=_sense_map[cut.sense], rhs=cut.rhs)

    def compute_iis(self) -> set[str]:
        self.model.computeIIS()

        # Variables
        iis_vars = set(
            v.getName() for v in self.model.getVars()
            if self.model.getVarLowerIIS(v) or self.model.getVarUpperIIS(v)
        )

        # Constraints
        for cons in self.model.getConstrs():
            is_in_iis = self.model.getConstrLowerIIS(cons) or self.model.getConstrUpperIIS(cons)
            if is_in_iis:
                expr = self.model.getRow(cons)
                for j in range(expr.getSize()):
                    var = expr.getVar(j)
                    iis_vars.add(var.getName())

        return iis_vars

    @staticmethod
    def make_master_problem(original_model: Model, master_vars: list[str]) -> Model:
        Copt.__check_objective_sense(original_model)
        master = original_model.clone()

        # Remove non-master variables & remove them from objective (will be handled automatically)
        non_master_vars = set(v.getName() for v in master.getVars()) - set(master_vars)
        for var_name in non_master_vars:
            var = master.getVarByName(var_name)
            master.remove(var)

        # Remove constraints that contains non-master variables
        _cons_to_remove_idx = []
        constrs = master.getConstrs()

        for idx, constr in enumerate(constrs):
            expr = master.getRow(constr)
            for i in range(expr.getSize()):
                var = expr.getVar(i)
                if var.getName() not in master_vars:
                    _cons_to_remove_idx.append(idx)
                    break

        # Execute removal
        for idx in reversed(_cons_to_remove_idx):
            master.remove(constrs[idx])

        return master

    @staticmethod
    def make_sub_problem(original_model: Model, master_vars: list[str]) -> Model:
        Copt.__check_objective_sense(original_model)
        sub = original_model.clone()
        sub.setObjConst(0)

        # Set master variables to continuous & remove them from objective
        for var_name in master_vars:
            var = sub.getVarByName(var_name)
            var.vtype = COPT.CONTINUOUS
            var.obj = 0

        # Remove constraints that contains only master variables
        _cons_to_remove_idx = []
        constrs = sub.getConstrs()

        for idx, constr in enumerate(constrs):
            expr = sub.getRow(constr)
            is_master_only = True
            for i in range(expr.getSize()):
                var = expr.getVar(i)
                if var.getName() not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_remove_idx.append(idx)

        # Execute removal
        for idx in reversed(_cons_to_remove_idx):
            sub.remove(constrs[idx])

        return sub
