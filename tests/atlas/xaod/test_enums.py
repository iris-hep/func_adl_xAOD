import ast
from enum import Enum

import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.atlas.xaod.query_ast_visitor import (
    atlas_xaod_query_ast_visitor,
)
from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore
from tests.utils.general import get_lines_of_code, print_lines
from tests.utils.locators import find_line_numbers_with


def test_ast_enum():
    "Test class an enum as a constant"
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])

    q = atlas_xaod_query_ast_visitor()
    r = q.get_rep(ast.parse("xAOD.Jet.Color.Red").body[0].value)  # type: ignore
    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == "xAOD.Jet.Color"
    assert r.as_cpp() == "xAOD::Jet::Red"


class xAOD:
    class Jet:
        class Color(Enum):
            Red = 1
            Blue = 2


def test_enum_return():
    """Test code-gen for a simple enum reference as a result"""
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "color",
        ctyp.terminal("xAOD::Jet::Color"),
    )
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.color() == xAOD.Jet.Color.Red)
        .Select(lambda j: j.pt())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    found_lines = find_line_numbers_with("->color()==xAOD::Jet::Red", lines)
    assert len(found_lines) == 1


def test_enum_arg():
    """Test code-gen for a simple enum reference as a method argument

    We test the result of `color` to be `True` because we don't have
    a full type model in this test.
    """
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "color",
        ctyp.terminal("bool"),
    )
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.color(xAOD.Jet.Color.Red) == True)  # noqa
        .Select(lambda j: j.pt())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    found_lines = find_line_numbers_with("->color(xAOD::Jet::Red)==true", lines)
    assert len(found_lines) == 1


def test_enum_output():
    """Test code-gen for a simple enum reference when it is returned from the client"""
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "color",
        ctyp.terminal("xAOD::Jet::Color", tree_type="int"),
    )
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.color())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure the fill variable is declared as an integer, and we cast the enum
    # to an integer before it is sent into the ROOT file.
    # It would be nice to use a enum here, but ROOT doesn't support it, and nor
    # does awkward.
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "int" == str(vs[0].cpp_type())
    n = find_line_numbers_with("static_cast<int>", lines)
    assert len(n) == 1
    assert "static_cast<int>(" in lines[n[0]]
    assert "->color())" in lines[n[0]]
