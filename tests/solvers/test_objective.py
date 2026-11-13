# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from contextlib import ExitStack
import sys

import pytest

from benderslib import AnnotatedBenders, BendersParams, ClassicalBenders, CST
from benderslib.errors import BendersNotImplementedError


@pytest.fixture(params=["gurobi", "copt", "cplex", "scip", "pyomo"])
def objective_model(request, constant):
    """Return an adapter, native model and native linear objective reader."""
    with ExitStack() as resources:
        if request.param == "gurobi":
            gp = pytest.importorskip("gurobipy")
            from benderslib.solvers import Gurobi

            solver = Gurobi
            env = resources.enter_context(gp.Env(params={"OutputFlag": 0}))
            model = resources.enter_context(gp.Model(env=env))
            x = model.addVar(vtype=gp.GRB.BINARY, name="x")
            y = model.addVar(name="y")
            model.addConstr(x + y >= 1, name="coupling")
            model.setObjective(x + 2 * y + constant)
            model.update()

            def objective(m):
                m.update()
                return m.ObjCon, {v.VarName: v.Obj for v in m.getVars()}

        elif request.param == "copt":
            cp = pytest.importorskip("coptpy")
            from benderslib.solvers import Copt

            solver = Copt
            env = cp.Envr()
            model = env.createModel()
            model.setParam(cp.COPT.Param.Logging, 0)
            x = model.addVar(vtype=cp.COPT.BINARY, name="x")
            y = model.addVar(name="y")
            model.addConstr(x + y >= 1, name="coupling")
            model.setObjective(x + 2 * y + constant)

            def objective(m):
                return m.getAttr(cp.COPT.Attr.ObjConst), {
                    v.getName(): v.obj for v in m.getVars()
                }

        elif request.param == "cplex":
            if (3, 13) <= sys.version_info < (3, 14):
                pytest.skip("GitHub Actions failed with CPLEX on Python 3.13.")
            cp = pytest.importorskip("cplex")
            from benderslib.solvers import Cplex

            solver = Cplex
            model = resources.enter_context(cp.Cplex())
            model.set_log_stream(None)
            model.set_results_stream(None)
            model.variables.add(names=["x", "y"], types="BC", ub=[1, cp.infinity], obj=[1, 2])
            model.objective.set_offset(constant)
            model.linear_constraints.add(
                lin_expr=[cp.SparsePair(ind=["x", "y"], val=[1, 1])],
                senses="G", rhs=[1], names=["coupling"],
            )

            def objective(m):
                return m.objective.get_offset(), dict(zip(
                    m.variables.get_names(), m.objective.get_linear()
                ))

        elif request.param == "scip":
            scip = pytest.importorskip("pyscipopt")
            from benderslib.solvers import Scip

            solver = Scip
            model = scip.Model()
            resources.callback(model.freeProb)
            model.hideOutput()
            x = model.addVar(vtype="B", name="x")
            y = model.addVar(name="y")
            model.addCons(x + y >= 1, name="coupling")
            model.setObjective(x + 2 * y + constant)

            def objective(m):
                return m.getObjoffset(), {
                    v.name: v.getObj() for v in m.getVars(transformed=False)
                }

        else:
            pyo = pytest.importorskip("pyomo.environ")
            from pyomo.repn import generate_standard_repn
            from benderslib.solvers import Pyomo

            class HighsPyomo(Pyomo):
                def __init__(self, model):
                    super().__init__(model, solver="highs")

            solver = HighsPyomo
            model = pyo.ConcreteModel()
            model.x = pyo.Var(domain=pyo.Binary, bounds=(0, 1))
            model.y = pyo.Var(domain=pyo.NonNegativeReals)
            model.obj = pyo.Objective(expr=model.x + 2 * model.y + constant)
            model.coupling = pyo.Constraint(expr=model.x + model.y >= 1)

            def objective(m):
                obj = next(m.component_data_objects(pyo.Objective, active=True))
                repn = generate_standard_repn(obj.expr)
                return pyo.value(repn.constant), {
                    v.name: pyo.value(c) for v, c in zip(repn.linear_vars, repn.linear_coefs)
                }

        def sense(m, maximize=False):
            if request.param == "gurobi":
                if maximize:
                    m.ModelSense = gp.GRB.MAXIMIZE
                m.update()
                return m.ModelSense == gp.GRB.MAXIMIZE
            if request.param == "copt":
                if maximize:
                    m.setObjSense(cp.COPT.MAXIMIZE)
                return m.objsense == cp.COPT.MAXIMIZE
            if request.param == "cplex":
                if maximize:
                    m.objective.set_sense(m.objective.sense.maximize)
                return m.objective.get_sense() == m.objective.sense.maximize
            if request.param == "scip":
                if maximize:
                    m.setMaximize()
                return m.getObjectiveSense() == "maximize"
            obj = next(m.component_data_objects(pyo.Objective, active=True))
            if maximize:
                obj.sense = pyo.maximize
            return obj.sense == pyo.maximize

        yield solver, model, objective, sense


@pytest.mark.parametrize("constant", [7, -7, 0])
@pytest.mark.parametrize("entrypoint", ["adapter", "native", "wrapped"])
def test_decomposition_objective_constant(objective_model, constant, entrypoint):
    solver, original, objective, sense = objective_model
    before = objective(original)
    if entrypoint == "adapter":
        master = solver.make_master_problem(original, ["x"])
        sub = solver.make_sub_problem(original, ["x"])
    else:
        master, sub = AnnotatedBenders.decompose(
            original, solver, ["x"], solver_model=entrypoint == "native"
        )
        if entrypoint == "wrapped":
            master, sub = master.model, sub.model

    assert not sense(master)
    assert not sense(sub)
    assert not sense(original)
    master_offset, master_coefs = objective(master)
    sub_offset, sub_coefs = objective(sub)
    assert master_offset == pytest.approx(constant)
    assert sub_offset == pytest.approx(0)
    assert master_coefs.get("x", 0) == pytest.approx(1)
    assert master_coefs.get("y", 0) == pytest.approx(0)
    assert sub_coefs.get("x", 0) == pytest.approx(0)
    assert sub_coefs.get("y", 0) == pytest.approx(2)
    for x in (0, 1):
        point = {"x": x, "y": 1 - x}
        split_value = master_offset + sub_offset + sum(
            (master_coefs.get(v, 0) + sub_coefs.get(v, 0)) * value
            for v, value in point.items()
        )
        assert split_value == pytest.approx(before[0] + sum(
            before[1][v] * value for v, value in point.items()
        ))
    assert objective(original) == before


@pytest.mark.parametrize("constant", [7, -7, 0])
def test_benders_objective_constant(objective_model, constant):
    solver, original, objective, sense = objective_model
    if solver.__name__ == "HighsPyomo":
        pytest.importorskip("highspy")
    before = objective(original)
    bd = AnnotatedBenders(
        original, solver=solver, complicating_vars=["x"], benders=ClassicalBenders,
        params=BendersParams(time_limit=30, iter_limit=20),
    )
    bd.solve()
    assert bd.result.status == CST.OPTIMAL
    assert bd.result.obj == pytest.approx(1 + constant)
    assert bd.result.lb == pytest.approx(1 + constant)
    assert bd.result.ub == pytest.approx(1 + constant)
    assert bd.result.solution == pytest.approx({"x": 1, "y": 0})
    assert objective(original) == before


@pytest.mark.parametrize("constant", [7])
@pytest.mark.parametrize("entrypoint", ["constructor", "master", "sub", "native", "wrapped"])
def test_maximization_rejected_before_decomposition(objective_model, entrypoint):
    solver, original, objective, sense = objective_model
    sense(original, maximize=True)
    before = objective(original)

    with pytest.raises(
        BendersNotImplementedError,
        match=r"BendersLib currently only supports minimization problems\.",
    ):
        if entrypoint == "constructor":
            solver(original)
        elif entrypoint == "master":
            solver.make_master_problem(original, ["x"])
        elif entrypoint == "sub":
            solver.make_sub_problem(original, ["x"])
        else:
            AnnotatedBenders.decompose(
                original, solver, ["x"], solver_model=entrypoint == "native"
            )

    assert sense(original)
    assert objective(original) == before
