import ast
from enum import Enum

import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from build.lib.func_adl_xAOD.atlas.xaod.query_ast_visitor import (
    atlas_xaod_query_ast_visitor,
)
from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore
from tests.utils.general import get_lines_of_code, print_lines


def test_ast_enum():
    "Test class an enum as a constant"

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
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)

    assert False, "Not implemented"


def test_enum_arg():
    """Test code-gen for a simple enum reference as a method argument

    We test the result of `color` to be `True` because we don't have
    a full type model in this test.
    """
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "color",
        ctyp.terminal("bool"),
    )
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.color(xAOD.Jet.Color.Red) is True)
        .Select(lambda j: j.pt())
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)

    assert False, "Not implemented"


def test_enum_output():
    """Test code-gen for a simple enum reference when it is returned from the client"""
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "color",
        ctyp.terminal("xAOD::Jet::Color"),
    )
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.color())
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)

    assert False, "Not implemented"
