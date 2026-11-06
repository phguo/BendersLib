import pytest

from benderslib.consts import BendersConsts as CST
from benderslib.solvers import CplexCP, Ortools


@pytest.fixture(params=["ortools", "cplexcp"])
def backend(request):
    if request.param == "ortools":
        cp = pytest.importorskip("ortools.sat.python.cp_model")
        model = cp.CpModel()
        x = model.new_int_var(-3, 3, "x")
        y = model.new_int_var(-3, 3, "y")
        return Ortools(model, {"x": x, "y": y})

    cp = pytest.importorskip("docplex.cp.model")
    model = cp.CpoModel()
    x = model.integer_var(-3, 3, name="x")
    y = model.integer_var(-3, 3, name="y")
    return CplexCP(model, {"x": x, "y": y}, cons_vars={})


def test_fix_vars_rounds_near_integers(backend):
    backend.fix_vars({"x": 0.999999999, "y": -1.999999999})
    backend.solve()
    assert backend.status == CST.OPTIMAL
    assert backend.get_var_values() == {"x": 1, "y": -2}


@pytest.mark.parametrize("invalid", [0.5, float("nan"), float("inf"), -float("inf")])
def test_invalid_fix_preserves_existing_model(backend, invalid):
    backend.fix_vars({"x": 1, "y": -2})
    fixed_model = backend.model
    with pytest.raises(ValueError, match="'y'"):
        backend.fix_vars({"x": 3, "y": invalid})
    assert backend.model is fixed_model
    backend.solve()
    assert backend.get_var_values() == {"x": 1, "y": -2}
