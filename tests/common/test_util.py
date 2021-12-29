import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.utils import most_accurate_type, parse_type


def test_accurate_type_single_int():
    t = ctyp.terminal('int', False)
    r = most_accurate_type([t])
    assert r._type == 'int'


def test_accurate_type_single_float():
    t = ctyp.terminal('float', False)
    r = most_accurate_type([t])
    assert r._type == 'float'


def test_accurate_type_two_int():
    t1 = ctyp.terminal('int', False)
    t2 = ctyp.terminal('int', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'int'


def test_accurate_type_int_and_float():
    t1 = ctyp.terminal('int', False)
    t2 = ctyp.terminal('float', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'float'


def test_accurate_type_float_and_double():
    t1 = ctyp.terminal('double', False)
    t2 = ctyp.terminal('float', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'double'


def test_parse_type_int():
    t = parse_type('int')
    assert t.name == 'int'
    assert t.pointer_depth == 0


def test_parse_type_int_sp():
    t = parse_type(' int  ')
    assert t.name == 'int'
    assert t.pointer_depth == 0


def test_parse_type_int_ptr():
    t = parse_type('int*')
    assert t.name == 'int'
    assert t.pointer_depth == 1


def test_parse_type_int_ptr_sp():
    t = parse_type('int  *')
    assert t.name == 'int'
    assert t.pointer_depth == 1


def test_parse_type_int_2ptr_sp():
    t = parse_type('int  *  *')
    assert t.name == 'int'
    assert t.pointer_depth == 2


def test_parse_type_str():
    t = parse_type('string')
    assert str(t) == 'string'


def test_parse_type_str_ptr():
    t = parse_type('string *')
    assert str(t) == 'string*'
