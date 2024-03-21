import ast
from enum import Enum

import pytest

from func_adl_xAOD.atlas.xaod.event_collections import (
    atlas_xaod_event_collection_collection,
)
import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.atlas.xaod.query_ast_visitor import atlas_xaod_query_ast_visitor
from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore
from tests.atlas.xaod.utils import as_pandas
from tests.utils.general import get_lines_of_code, print_lines
from tests.utils.locators import find_line_numbers_with

from .config import f_exot_15, run_long_running_tests


def test_ast_enum():
    "Test class an enum as a constant"
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])

    q = atlas_xaod_query_ast_visitor()
    r = q.get_rep(ast.parse("xAOD.Jet.Color.Red").body[0].value)  # type: ignore
    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == "xAOD.Jet.Color"
    assert r.as_cpp() == "xAOD::Jet::Red"


def test_ast_enum_no_value():
    "Test class an enum as a constant"
    ctyp.define_enum("xAOD.Jet", "Color", ["Red", "Blue"])

    with pytest.raises(ValueError) as e:
        q = atlas_xaod_query_ast_visitor()
        q.get_rep(ast.parse("xAOD.Jet.Color.Red.value").body[0].value)  # type: ignore

    assert "xAOD.Jet.Color" in str(e.value)
    assert ".value" in str(e.value)


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


@run_long_running_tests
def test_class_enum_use_as_argument():
    """Run an actual return thing that will generate some output that we can
    examine on a test sample.
    """

    # Define the calo clusters return
    from func_adl_xAOD.atlas.xaod.event_collections import (
        atlas_xaod_collections,
    )

    atlas_xaod_collections.append(
        EventCollectionSpecification(
            "atlas",
            "CaloClusters",
            ["xAODCaloEvent/CaloClusterContainer.h"],
            atlas_xaod_event_collection_collection(
                "xAOD::CaloClusterContainer", "xAOD::CaloCluster"
            ),
            ["xAODCaloEvent"],
        ),
    )

    # Define the num class for future reference
    class ClusterSize(Enum):
        SW_55ele = 1
        SW_35ele = 2
        SW_37ele = 3
        SW_55gam = 4
        SW_35gam = 5
        SW_37gam = 6
        SW_55Econv = 7
        SW_35Econv = 8
        SW_37Econv = 9
        SW_softe = 10
        Topo_420 = 11
        Topo_633 = 12
        SW_7_11 = 13
        SuperCluster = 14
        Tower_01_01 = 15
        Tower_005_005 = 16
        Tower_fixed_area = 17
        CSize_Unknown = 99

    # Declare the enum class
    ctyp.define_enum(
        "xAOD.CaloCluster_v1", "ClusterSize", [e.name for e in ClusterSize]
    )

    # Define the `getConstituentsSignalState` method
    ctyp.add_method_type_info(
        "xAOD::CaloCluster_v1",
        "clusterSize",
        ctyp.terminal("xAOD::CaloCluster_v1::ClusterSize", tree_type="int"),
    )

    # fmt: off
    training_df = as_pandas(
        f_exot_15.SelectMany(lambda e: e.CaloClusters("egammaClusters"))
        .Select(lambda c: c.clusterSize())
    )
    # fmt: on

    assert len(training_df) > 0
    print(training_df.col1)
    assert all(training_df.col1 == ClusterSize.SuperCluster.value)


@run_long_running_tests
def test_class_enum_use_inline():
    """Use a enum as part of the actual query"""

    # Define the calo clusters return
    from func_adl_xAOD.atlas.xaod.event_collections import (
        atlas_xaod_collections,
    )

    atlas_xaod_collections.append(
        EventCollectionSpecification(
            "atlas",
            "CaloClusters",
            ["xAODCaloEvent/CaloClusterContainer.h"],
            atlas_xaod_event_collection_collection(
                "xAOD::CaloClusterContainer", "xAOD::CaloCluster"
            ),
            ["xAODCaloEvent"],
        ),
    )

    # Define the num class for future reference
    class xAOD:
        class CaloCluster_v1:
            class ClusterSize(Enum):
                SW_55ele = 1
                SW_35ele = 2
                SW_37ele = 3
                SW_55gam = 4
                SW_35gam = 5
                SW_37gam = 6
                SW_55Econv = 7
                SW_35Econv = 8
                SW_37Econv = 9
                SW_softe = 10
                Topo_420 = 11
                Topo_633 = 12
                SW_7_11 = 13
                SuperCluster = 14
                Tower_01_01 = 15
                Tower_005_005 = 16
                Tower_fixed_area = 17
                CSize_Unknown = 99

    # Declare the enum class
    ctyp.define_enum(
        "xAOD.CaloCluster_v1",
        "ClusterSize",
        [e.name for e in xAOD.CaloCluster_v1.ClusterSize],
    )

    # Define the `getConstituentsSignalState` method
    ctyp.add_method_type_info(
        "xAOD::CaloCluster_v1",
        "clusterSize",
        ctyp.terminal("xAOD::CaloCluster_v1::ClusterSize", tree_type="int"),
    )

    # fmt: off
    training_df = as_pandas(
        f_exot_15.SelectMany(lambda e: e.CaloClusters("egammaClusters"))
        .Select(lambda c: c.clusterSize() == xAOD.CaloCluster_v1.ClusterSize.SuperCluster)
    )
    # fmt: on

    assert len(training_df) > 0
    print(training_df.col1)
    assert all(training_df.col1 == True)  # noqa
