import pytest

from benderslib import ClassicalBenders, MasterProblem, SubProblem
from benderslib.consts import BendersConsts as CST
from benderslib.core import FeasibilityCut
from benderslib.errors import BendersBackendError
from benderslib.solvers import Pyomo

pyo = pytest.importorskip("pyomo.environ")


def make_model():
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.cost = pyo.Objective(expr=model.x)
    return model


def test_classical_cut_uses_constraint_body_offset():
    pytest.importorskip("gurobipy")
    master = make_model()
    master.cost.expr = 0.5 * master.x
    sub = make_model()
    sub.y = pyo.Var(domain=pyo.NonNegativeReals)
    sub.cost.expr = sub.y
    sub.demand = pyo.Constraint(expr=sub.x + sub.y + 5 >= 10)
    bd = ClassicalBenders(
        MasterProblem(Pyomo(master, "gurobi_direct")),
        SubProblem(Pyomo(sub, "gurobi_direct")),
        ["x"],
    )
    bd.solve()
    assert bd.result.status == CST.OPTIMAL
    assert bd.result.obj == pytest.approx(2.5)


@pytest.mark.parametrize("lower", [-10, 3])
def test_estimator_respects_lower_bound(lower):
    pytest.importorskip("gurobipy")
    model = make_model()
    backend = Pyomo(model, "gurobi_direct")
    backend.add_estimators(["theta"], lb=lower)
    backend.solve()
    assert backend.get_var_values(["theta"])["theta"] == pytest.approx(lower)


def test_remove_cut_updates_persistent_model():
    pytest.importorskip("gurobipy")
    master = MasterProblem(Pyomo(make_model(), "gurobi_persistent"))
    name = master.add_cut(FeasibilityCut(["x"], [1], 5, ">="))
    master.solve()
    assert master.get_obj() == pytest.approx(5)
    master.remove_cut(name)
    master.solve()
    assert master.get_obj() == pytest.approx(0)
    assert not master.cuts
    assert not master.feasibility_cuts


@pytest.mark.parametrize("multiple", [False, True])
def test_requires_one_active_objective(multiple):
    model = make_model()
    if multiple:
        model.other = pyo.Objective(expr=2 * model.x)
    else:
        model.cost.deactivate()
    with pytest.raises(BendersBackendError, match="exactly one active objective"):
        Pyomo(model, "gurobi_direct")
