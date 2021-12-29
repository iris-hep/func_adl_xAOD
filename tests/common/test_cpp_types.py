import func_adl_xAOD.common.cpp_types as ctyp


def test_int():
    t_int = ctyp.terminal('int')
    assert t_int.is_pointer() is False


def test_int_pointer():
    t_int = ctyp.terminal('int', p_depth=1)
    assert t_int.is_pointer() is True


def test_no_method_type_found():
    assert ctyp.method_type_info("bogus", "pt") is None


def test_method_type_found():
    ctyp.add_method_type_info("bogus", "pt", ctyp.terminal('double'))
    assert 'double' == str(ctyp.method_type_info("bogus", "pt"))


def test_terminal_type():
    t = ctyp.terminal('double', False)
    assert t.type == 'double'


def test_terminal_from_parse():
    t = ctyp.terminal(ctyp.parse_type('double'))

    assert t.type == 'double'
    assert t.is_pointer() is False


def test_terminal_from_parse_ptr():
    t = ctyp.terminal(ctyp.parse_type('double*'))

    assert t.type == 'double'
    assert t.is_pointer() is True


def test_collection():
    c = ctyp.collection(ctyp.terminal('double'), p_depth=0)
    assert c.type == 'std::vector<double>'
    assert c.p_depth == 0


def test_collection_with_arr_type():
    c = ctyp.collection(ctyp.terminal('double'), 'VectorOfFloats', 0)
    assert c.type == 'VectorOfFloats'
    assert c.p_depth == 0


def test_collection_with_arr_type_parsed():
    c = ctyp.collection(ctyp.terminal('double'), ctyp.parse_type('VectorOfFloats*'))
    assert c.type == 'VectorOfFloats'
    assert c.p_depth == 1


def test_parse_type_int():
    t = ctyp.parse_type('int')
    assert t.name == 'int'
    assert t.pointer_depth == 0


def test_parse_type_int_sp():
    t = ctyp.parse_type(' int  ')
    assert t.name == 'int'
    assert t.pointer_depth == 0


def test_parse_type_int_ptr():
    t = ctyp.parse_type('int*')
    assert t.name == 'int'
    assert t.pointer_depth == 1


def test_parse_type_int_ptr_sp():
    t = ctyp.parse_type('int  *')
    assert t.name == 'int'
    assert t.pointer_depth == 1


def test_parse_type_int_2ptr_sp():
    t = ctyp.parse_type('int  *  *')
    assert t.name == 'int'
    assert t.pointer_depth == 2


def test_parse_type_str():
    t = ctyp.parse_type('string')
    assert str(t) == 'string'


def test_parse_type_str_ptr():
    t = ctyp.parse_type('string *')
    assert str(t) == 'string*'
