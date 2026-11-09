# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from unittest.mock import Mock, patch

import pytest

from benderslib import (
    AnnotatedBenders, BendersParams, CombinatorialBenders, CombinatorialOC,
    IntegerLShaped, MasterProblem, NoGoodFC, SubProblem, SubProblems,
)
from benderslib.cuts import (
    CombinatorialFCGen,
    CombinatorialOCGen,
    IntegerLShapedFCGen,
    IntegerLShapedOCGen,
)
from benderslib.errors import BendersCutError, NonBinaryVariableValueError
from benderslib.utils import is_all_binary


@pytest.mark.parametrize("values, tol, expected", [
    ([], 1e-5, True), ([0, 1, 0.0, 1.0], 0, True),
    ([-5e-6, 1.000005], 1e-5, True), ([0.0005], 1e-3, True),
    ([0.0005], 1e-5, False), ([1e-12], 0, False),
    ([0, 2], 1e-5, False), ([-1], 1e-5, False), ([0.5], 1e-5, False),
    ([float('nan')], 1e-5, False), ([float('inf')], 1e-5, False),
    ([-float('inf')], 1e-5, False),
    ([-0.25, 1.25], 0.25, True), ([0.5], 0.499999, False),
])
def test_is_all_binary(values, tol, expected):
    assert is_all_binary(values, tol) is expected


@pytest.fixture(params=[NoGoodFC, CombinatorialOC])
def make_cut(request):
    def create(values, **kwargs):
        if request.param is CombinatorialOC:
            return CombinatorialOC(values, 10, **kwargs)
        return NoGoodFC(values, **kwargs)
    return create


@pytest.mark.parametrize("value", [-1, 2, 0.25, 0.5, 0.75, -2e-5, 1.00002,
                                       float('nan'), float('inf'), -float('inf')])
def test_nonbinary_values_raise_cut_error(make_cut, value):
    with pytest.raises(NonBinaryVariableValueError) as exc_info:
        make_cut({'valid': 1, 'x': value})
    error = exc_info.value
    assert isinstance(error, BendersCutError)
    assert error.code == 5002
    assert error.context == {'tol_binary': BendersParams.tol_binary}


def test_error_does_not_print_variable_values(make_cut):
    values = {f'long_variable_name_{i}': 0 for i in range(1000)}
    values['invalid_variable'] = 2
    with pytest.raises(NonBinaryVariableValueError) as exc_info:
        make_cut(values)
    error = exc_info.value
    assert error.context == {'tol_binary': BendersParams.tol_binary}
    assert 'long_variable_name' not in str(error)
    assert 'invalid_variable' not in str(error)


@pytest.mark.parametrize("tol, delta", [
    (None, 5e-6), (0, 0), (1e-3, 5e-4), (0.125, 0.125), (0.25, 0.25),
])
def test_binary_values_preserve_cut_and_input(make_cut, tol, delta):
    exact = {'zero': 0, 'one': 1}
    values = {'zero': -delta, 'one': 1 + delta}
    original = values.copy()
    cut = make_cut(values, **({} if tol is None else {'tol_binary': tol}))
    expected = make_cut(exact)
    assert (cut.vars, cut.coefs, cut.rhs, cut.sense) == (
        expected.vars, expected.coefs, expected.rhs, expected.sense)
    assert values == original


@pytest.mark.parametrize("tol, value", [
    (0, 1e-12), (1e-3, 0.002), (0.125, 1.25), (0.499999, 0.5),
])
def test_configured_tolerance_rejects_outside_values(make_cut, tol, value):
    with pytest.raises(NonBinaryVariableValueError):
        make_cut({'x': value}, tol_binary=tol)


@pytest.mark.parametrize("tol", [-1e-5, 0.5, 0.500001, 1, float('nan'), float('inf'), -float('inf')])
def test_invalid_tolerance(make_cut, tol):
    with pytest.raises(ValueError, match='tol_binary'):
        make_cut({'x': 0}, tol_binary=tol)
    with pytest.raises(ValueError, match='tol_binary'):
        is_all_binary([], tol)


@pytest.mark.parametrize("generator_class, multi", [
    (CombinatorialFCGen, False), (CombinatorialOCGen, False),
    (IntegerLShapedFCGen, False), (IntegerLShapedOCGen, False),
    (IntegerLShapedOCGen, True),
])
def test_generators_pass_tolerance_and_validate_original_values(generator_class, multi):
    master = Mock(complicating_vars=['x'], estimators=['theta'])
    master.get_var_values.return_value = {'x': 0.0005}
    master.get_estimator_values.return_value = {'theta': 0}
    sub = Mock(complicating_vars=['x'])
    sub.get_obj.return_value = 10
    if multi:
        sub = Mock(complicating_vars=['x'], __iter__=Mock(return_value=iter([sub])))
    params = BendersParams(tol_binary=1e-3, multi_opti_cut=multi)
    generator = generator_class(master, sub, params)
    assert len(generator.generate()) == 1

    # Recreate the iterator because generate() consumes the multi-cut scenarios.
    if multi:
        sub.__iter__.return_value = iter([Mock(get_obj=Mock(return_value=10))])
    params.tol_binary = 1e-5
    with pytest.raises(NonBinaryVariableValueError):
        generator.generate()


@pytest.mark.parametrize("entrypoint", ['constructor', 'from_models', 'annotated'])
@pytest.mark.parametrize("method, multi", [
    (CombinatorialBenders, False), (IntegerLShaped, False), (IntegerLShaped, True),
])
def test_outer_params_reach_binary_cut_construction(entrypoint, method, multi):
    params = BendersParams(tol_binary=1e-3, multi_opti_cut=multi)
    master_backend = Mock()
    master_backend.get_var_values.side_effect = lambda names: {
        name: (0.0005 if name == 'x' else 0) for name in names
    }
    sub_backend = Mock(get_obj=Mock(return_value=10))
    stochastic = method is IntegerLShaped

    if entrypoint == 'from_models':
        benders = method.from_models(
            object(), Mock(return_value=master_backend),
            [object()] if stochastic else object(), Mock(return_value=sub_backend),
            ['x'], params=params,
        )
    else:
        master = MasterProblem(master_backend)
        sub = SubProblem(sub_backend)
        if stochastic:
            sub = SubProblems([sub])
        if entrypoint == 'annotated':
            with patch.object(AnnotatedBenders, 'decompose', return_value=(master, sub)):
                benders = AnnotatedBenders(object(), Mock(), ['x'], benders=method, params=params)
        else:
            benders = method(master, sub, ['x'], params=params)

    benders.master_problem.estimators = ['theta']
    assert benders.params is params
    for generator in (benders.optimality_cut, benders.feasibility_cut):
        assert generator.params is params
        cuts = generator._generate()
        assert len(cuts) == 1
        assert cuts[0]._params is params

    # Changing the outer parameter after initialization must affect validation too.
    benders.params.tol_binary = 1e-5
    for generator in (benders.optimality_cut, benders.feasibility_cut):
        with pytest.raises(NonBinaryVariableValueError) as exc_info:
            generator._generate()
        assert exc_info.value.context['tol_binary'] == 1e-5
