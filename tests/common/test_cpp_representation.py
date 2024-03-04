import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
import pytest
from func_adl_xAOD.common.util_scope import gc_scope_top_level, top_level_scope


def test_expression_pointer_decl():
    e2 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int"))
    assert e2.p_depth == 0

    e3 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int", p_depth=1))
    assert e3.p_depth == 1


def test_cpp_value_as_str():
    "Make sure we can generate a str from a value - this will be important for errors"
    v1 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int"))
    assert "dude" in str(v1)

    v2 = crep.cpp_value("dude", top_level_scope(), None)
    assert "dude" in str(v2)


def test_variable_type_update():
    tc = gc_scope_top_level()
    expr = "a"
    ctype = ctyp.terminal("int", False)

    v = crep.cpp_variable(expr, tc, ctype)
    v.update_type(ctyp.terminal("float", False))

    assert v.cpp_type().type == "float"


def test_variable_pointer():
    "Make sure p_depth can deal with a non-type correctly"
    v1 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int"))
    v2 = crep.cpp_value("dude", top_level_scope(), None)

    assert v1.p_depth == 0
    with pytest.raises(RuntimeError):
        v2.p_depth


def test_variable_pointer_2():
    "Make sure p_depth can deal with a non-type correctly"
    v1 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int"))
    v2 = crep.cpp_value("dude", top_level_scope(), None)

    assert v1.cpp_type().type == "int"
    with pytest.raises(RuntimeError):
        v2.cpp_type()


def test_variable_type__with_initial_update():
    tc = gc_scope_top_level()
    expr = "a"
    c_type = ctyp.terminal("int", False)
    c_init = crep.cpp_value("0.0", tc, ctyp.terminal("int", False))

    v = crep.cpp_variable(expr, tc, c_type, c_init)
    v.update_type(ctyp.terminal("float", False))

    assert v.cpp_type().type == "float"
    iv = v.initial_value()
    assert iv is not None
    assert iv.cpp_type().type == "float"


def test_sequence_type():
    tc = gc_scope_top_level()
    s_value = crep.cpp_value("0.0", tc, ctyp.terminal("int", False))
    i_value = crep.cpp_value("1.0", tc, ctyp.terminal("object", False))

    seq = crep.cpp_sequence(s_value, i_value, tc)

    assert seq.sequence_value().cpp_type().type == "int"


def test_sequence_type_2():
    tc = gc_scope_top_level()
    s_value = crep.cpp_value("0.0", tc, ctyp.terminal("int", False))
    i_value = crep.cpp_value("1.0", tc, ctyp.terminal("object", False))

    seq = crep.cpp_sequence(s_value, i_value, tc)
    seq_array = crep.cpp_sequence(seq, i_value, tc)

    assert seq_array.sequence_value().cpp_type().type == "std::vector<int>"


def test_deref_simple_ptr():
    tc = gc_scope_top_level()
    expr = "a"
    c_type = ctyp.terminal("int", 1)

    v = crep.cpp_variable(expr, tc, c_type)

    d = crep.dereference_var(v)

    assert d.cpp_type().type == "int"
    assert d.cpp_type().p_depth == 0
    assert d.as_cpp() == "*a"


def test_deref_simple_no_ptr():
    tc = gc_scope_top_level()
    expr = "a"
    c_type = ctyp.terminal("int", 0)

    v = crep.cpp_variable(expr, tc, c_type)

    d = crep.dereference_var(v)

    assert d.cpp_type().type == "int"
    assert d.cpp_type().p_depth == 0
    assert d.as_cpp() == "a"


def test_deref_collection():
    tc = gc_scope_top_level()

    c_type = ctyp.collection(
        ctyp.terminal(ctyp.parse_type("int")), ctyp.parse_type("vector<int>")
    )
    c = crep.cpp_collection("my_var", tc, c_type)

    d = crep.dereference_var(c)

    assert isinstance(d, crep.cpp_collection)
    cpp_type = d.cpp_type()
    assert isinstance(cpp_type, ctyp.collection)
    assert str(cpp_type) == "vector<int>"
    assert str(cpp_type.element_type) == "int"


def test_deref_collection_ptr():
    tc = gc_scope_top_level()

    c_type = ctyp.collection(
        ctyp.terminal(ctyp.parse_type("int")), ctyp.parse_type("vector<int>*")
    )
    c = crep.cpp_collection("my_var", tc, c_type)

    d = crep.dereference_var(c)

    assert isinstance(d, crep.cpp_collection)
    cpp_type = d.cpp_type()
    assert isinstance(cpp_type, ctyp.collection)
    assert str(cpp_type) == "vector<int>"
    assert str(cpp_type.element_type) == "int"


def test_member_access_obj():
    cv = crep.cpp_value(
        "f", gc_scope_top_level(), ctyp.terminal(ctyp.parse_type("obj"))
    )
    assert crep.base_type_member_access(cv) == "f."


def test_member_access_obj_ptr():
    cv = crep.cpp_value(
        "f", gc_scope_top_level(), ctyp.terminal(ctyp.parse_type("obj*"))
    )
    assert crep.base_type_member_access(cv) == "f->"


def test_member_access_obj_ptr_ptr():
    cv = crep.cpp_value(
        "f", gc_scope_top_level(), ctyp.terminal(ctyp.parse_type("obj**"))
    )
    assert crep.base_type_member_access(cv) == "(*f)->"


def test_member_access_obj_depth_1():
    cv = crep.cpp_value(
        "f", gc_scope_top_level(), ctyp.terminal(ctyp.parse_type("obj"))
    )
    assert crep.base_type_member_access(cv, 2) == "(*f)->"


def test_ns_scope():
    "The NS scope is always top level - defined everywhere"
    cr = crep.cpp_namespace(ctyp.NameSpaceInfo("bogus"))
    assert cr.scope().is_top_level()


def test_ns_str():
    "NS should be readable"
    cr = crep.cpp_namespace(ctyp.NameSpaceInfo("bogus"))
    assert str(cr) == "cpp_namespace(bogus)"
