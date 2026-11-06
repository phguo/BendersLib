import json

import pytest

from benderslib import BendersParams, BendersResult, ClassicalBenders, LShaped, MasterProblem, OracleBenders
from benderslib.consts import BendersConsts as CST
from benderslib.errors import BendersSolverError
from benderslib.solvers import Gurobi


@pytest.fixture
def models():
    gp = pytest.importorskip("gurobipy")
    with gp.Env(params={"OutputFlag": 0}) as env:
        master = gp.Model(env=env)
        x = master.addVar(vtype=gp.GRB.INTEGER, ub=4, name="x")
        z = master.addVar(lb=3, name="z")
        master.setObjective(x + z)
        sub = gp.Model(env=env)
        sx = sub.addVar(name="x")
        y = sub.addVar(name="y")
        sub.addConstr(sx + y >= 2)
        sub.setObjective(2 * y)
        sub.update()
        yield master, sub


@pytest.mark.parametrize("first, second", [("solve", "solve"), ("solve", "bnc_solve"),
                                          ("bnc_solve", "solve"), ("bnc_solve", "bnc_solve")])
def test_incumbent_and_repeated_solve(models, first, second):
    master, sub = models
    bd = ClassicalBenders.from_models(master, Gurobi, sub, Gurobi, ["x"], params=BendersParams())
    getattr(bd, first)()
    assert bd.result.status == CST.OPTIMAL
    assert bd.result.solution == pytest.approx({"x": 2, "y": 0, "z": 3})
    master.update()
    variable_count = master.NumVars
    with pytest.raises(BendersSolverError, match="new BendersSolver instance"):
        getattr(bd, second)()
    master.update()
    assert master.NumVars == variable_count
    assert bd.result.solution == pytest.approx({"x": 2, "y": 0, "z": 3})


def test_scenario_solution_includes_master_values(models):
    master, sub = models
    bd = LShaped.from_models(master, Gurobi, [sub, sub.copy()], Gurobi, ["x"])
    bd.solve()
    assert bd.result.status == CST.OPTIMAL
    assert set(bd.result.solution) == {0, 1}
    for values in bd.result.solution.values():
        assert values == pytest.approx({"x": 2, "y": 0, "z": 3})


def test_oracle_solution_includes_master_values(models):
    master, _ = models
    bd = OracleBenders(MasterProblem(Gurobi(master)), lambda _: ([], 0, {"y": 2}), ["x"])
    bd.solve()
    assert bd.result.status == CST.OPTIMAL
    assert bd.result.solution == pytest.approx({"x": 0, "y": 2, "z": 3})


@pytest.mark.parametrize("status", [CST.OPTIMAL, CST.INFEASIBLE, CST.TIMEOUT])
def test_save_result_includes_status(tmp_path, status):
    path = tmp_path / "result.json"
    BendersResult(status=status).save(path)
    assert json.loads(path.read_text())["status"] == status
