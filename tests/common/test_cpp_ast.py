import ast

import pytest
from func_adl_xAOD.common.cpp_ast import (CPPCodeSpecification, CPPCodeValue,
                                          build_CPPCodeValue)
from func_adl_xAOD.common.math_utils import DeltaR
from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore


def test_deltaR_call():
    r = atlas_xaod_dataset().Select(lambda e: DeltaR(1.0, 1.0, 1.0, 1.0)).value()
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test__bad_deltaR_call():
    with pytest.raises(ValueError):
        atlas_xaod_dataset().Select(lambda e: DeltaR(1.0, 1.0, 1.0)).value()  # type: ignore


def test_build_cpp_cv_function():
    'Test building and modifying a callback function'

    func = CPPCodeSpecification(
        name='my_func',
        include_files=['my_include.h'],
        arguments=['a', 'b'],
        code=['auto result = a + b;'],
        result='result',
        cpp_return_type='double'
    )

    call_node = ast.parse('my_func(1, 2)').body[0].value  # type: ignore

    r = build_CPPCodeValue(func, call_node)

    assert isinstance(r.func, CPPCodeValue)
    assert r.func.replacement_instance_obj is None


def test_build_cpp_cv_function_bad_method():
    'Test building and modifying a callback function'

    func = CPPCodeSpecification(
        name='my_func',
        include_files=['my_include.h'],
        arguments=['a', 'b'],
        code=['auto result = a + b;'],
        result='result',
        cpp_return_type='double'
    )

    call_node = ast.parse('e.my_func(1, 2)').body[0].value  # type: ignore

    with pytest.raises(ValueError) as e:
        build_CPPCodeValue(func, call_node)

    assert "method" in str(e.value)


def test_build_cpp_cv_method():
    'Test building and modifying a callback function'

    func = CPPCodeSpecification(
        name='my_func',
        include_files=['my_include.h'],
        arguments=['a', 'b'],
        code=['auto result = a + b;'],
        result='result',
        cpp_return_type='double',
        method_object='obj_j',
        instance_object='xAOD::Jet_v1'
    )

    call_node = ast.parse('e.my_func(1, 2)').body[0].value  # type: ignore

    r = build_CPPCodeValue(func, call_node)

    assert isinstance(r.func, CPPCodeValue)
    assert r.func.replacement_instance_obj is not None


def test_build_cpp_cv_method_as_function():
    'Test building and modifying a callback function'

    func = CPPCodeSpecification(
        name='my_func',
        include_files=['my_include.h'],
        arguments=['a', 'b'],
        code=['auto result = a + b;'],
        result='result',
        cpp_return_type='double',
        method_object='obj_j',
        instance_object='xAOD::Jet_v1'
    )

    call_node = ast.parse('my_func(1, 2)').body[0].value  # type: ignore

    with pytest.raises(ValueError) as e:
        build_CPPCodeValue(func, call_node)

    assert "function" in str(e)
