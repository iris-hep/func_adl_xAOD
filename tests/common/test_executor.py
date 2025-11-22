import ast
from dataclasses import dataclass
from func_adl_xAOD.atlas.xaod.query_ast_visitor import atlas_xaod_query_ast_visitor
from typing import Any, Callable, Dict, List
from func_adl_xAOD.common.event_collections import (
    EventCollectionSpecification,
    event_collection_coder,
    event_collection_container,
)
from func_adl_xAOD.common.cpp_ast import CPPCodeValue, cpp_variable
from func_adl_xAOD.common.cpp_types import method_type_info

from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.executor import executor


class dummy_event_collection_coder(event_collection_coder):
    def get_running_code(self, container_type: event_collection_container) -> List[str]:
        return [f"{container_type} result = dude;"]


class do_nothing_executor(executor):
    def __init__(self, extended_md: Dict[str, Any] = {}):
        super().__init__([], "stuff.sh", "dude", {}, extended_md)

    def get_visitor_obj(self) -> query_ast_visitor:
        return atlas_xaod_query_ast_visitor()

    def build_collection_callback(
        self, metadata: EventCollectionSpecification
    ) -> Callable[[ast.Call], ast.Call]:
        ecc = dummy_event_collection_coder()
        return lambda cd: ecc.get_collection(metadata, cd)


def parse_statement(st: str) -> ast.AST:
    "Returns the interior of a parsed python statement as ast"
    return ast.parse(st).body[0].value  # type: ignore


def test_metadata_method():
    "Make sure the metadata call is properly dealt with"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_method_type_info", '
        '"type_string": "my_namespace::obj", '
        '"method_name": "pT", '
        '"return_type": "int", '
        "}), lambda e: e + 1)"
    )
    a2 = parse_statement("Select(ds, lambda e: e + 1)")

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert ast.dump(a2) == ast.dump(new_a1)

    t = method_type_info("my_namespace::obj", "pT")
    assert t is not None
    assert t.r_type.type == "int"
    assert not t.r_type.is_a_pointer


def test_metadata_method_2_clean():
    "Make sure we lose type information between calls"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_method_type_info", '
        '"type_string": "my_namespace::obj", '
        '"method_name": "pT", '
        '"return_type": "int", '
        "}), lambda e: e + 1)"
    )
    exe = do_nothing_executor()
    _ = exe.apply_ast_transformations(a1)
    exe.reset()

    a2 = parse_statement("Select(ds, lambda e: e + 1)")
    _ = exe.apply_ast_transformations(a2)
    t = method_type_info("my_namespace::obj", "pT")
    assert t is None


def test_metadata_cpp_code():
    "Make sure the metadata from a C++ bit of code is correctly put into type system"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"return_type": "double"'
        "}), lambda e: MyDeltaR(1,2,3,4))"
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)


def test_metadata_cpp_code_clean_second():
    "Make sure functions aren't remembers between calls"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"return_type": "double"'
        "}), lambda e: MyDeltaR(1,2,3,4))"
    )

    exe = do_nothing_executor()
    _ = exe.apply_ast_transformations(a1)

    a2 = parse_statement("Select(ds, lambda e: MyDeltaR(1,2,3,4))")
    new_a2 = exe.apply_ast_transformations(a2)

    assert "CPPCodeValue" not in ast.dump(new_a2)


def test_metadata_cpp_code_unneeded():
    "Make sure the metadata from a C++ bit of code is correctly put into type system"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"return_type": "double"'
        "}), lambda e: MyDeltaRR(1,2,3,4))"
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" not in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, ast.Name)


def test_metadata_cpp_code_method(mocker):
    "Run a method"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"method_object": "obj_j",'
        '"instance_object": "xAOD::Jet_v1",'
        '"return_type": "double",'
        "}), lambda e: e.MyDeltaR(1,2,3,4))"
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)

    # Check that the terminal type that is created is "ok".
    scope_mock = mocker.Mock()
    assert call_obj.result_rep is not None
    r = call_obj.result_rep(scope_mock)
    assert isinstance(r, cpp_variable)
    assert r.cpp_type().type == "double"
    assert r.p_depth == 0


def test_metadata_cpp_code_method_pointer(mocker):
    "Run method with a pointer"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": [],'
        '"arguments": [],'
        '"code": ['
        '   "static int holder = 10;",'
        '   "auto result = &holder;"'
        "],"
        '"method_object": "obj_j",'
        '"instance_object": "xAOD::Jet_v1",'
        '"return_type": "double*",'
        "}), lambda e: e.MyDeltaR())",
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)

    # Check that the terminal type that is created is "ok".
    scope_mock = mocker.Mock()
    assert call_obj.result_rep is not None
    r = call_obj.result_rep(scope_mock)
    assert isinstance(r, cpp_variable)
    assert r.cpp_type().type == "double"
    assert r.p_depth == 1


def test_metadata_cpp_code_capture():
    "Make sure we do not capture bad data (bug seen)"

    a1 = parse_statement(
        "Select(MetaData(MetaData(ds, {"
        '"metadata_type": "add_job_script",'
        '"name": "apply_corrections",'
        '"script": ["line1"],'
        '"depends_on": [],'
        "}),{"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"return_type": "double"'
        "}), lambda e: MyDeltaR(1,2,3,4))"
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)


def test_metadata_cpp_code_capture_2_clean():
    "Make sure we do not capture bad data (bug seen)"

    a1 = parse_statement(
        "Select(MetaData(MetaData(ds, {"
        '"metadata_type": "add_job_script",'
        '"name": "apply_corrections",'
        '"script": ["line1"],'
        '"depends_on": [],'
        "}),{"
        '"metadata_type": "add_cpp_function",'
        '"name": "MyDeltaR",'
        '"include_files": ["TVector2.h", "math.h"],'
        '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
        '"code": ['
        '   "auto d_eta = eta1 - eta2;",'
        '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
        '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
        "],"
        '"return_type": "double"'
        "}), lambda e: MyDeltaR(1,2,3,4))"
    )

    exe = do_nothing_executor()
    _ = exe.apply_ast_transformations(a1)
    assert len(exe._job_option_blocks) == 1
    exe.reset()
    assert len(exe._job_option_blocks) == 0


def test_metadata_collection():
    "Make sure the metadata for a new collections goes all the way through"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "add_atlas_event_collection_info",'
        '"name": "crazy",'
        '"include_files": ["xAODEventInfo/EventInfo.h"],'
        '"container_type": "xAOD::EventInfo",'
        '"contains_collection": True,'
        '"element_type": "Fork",'
        '}), lambda e: e.crazy("fork").pT())'
    )

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert "CPPCodeValue" in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func.value.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)
    assert "dude" in "-".join(call_obj.running_code)


def test_include_files():
    "Make sure include files are properly dealt with"

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "inject_code",'
        '"name": "crazy_fork",'
        '"body_includes": ["xAODEventInfo/EventInfo.h"],'
        '"header_includes": ["file.hpp"],'
        '}), lambda e: e.crazy("fork").pT())'
    )

    exe = do_nothing_executor()
    _ = exe.apply_ast_transformations(a1)
    assert exe.body_include_files == ["xAODEventInfo/EventInfo.h"]
    assert exe.header_include_files == ["file.hpp"]


def test_extended_md():
    "Make sure we can add extended md parsing"

    @dataclass
    class MyMD:
        "My metadata"

        name: str
        value: str

    a1 = parse_statement(
        "Select(MetaData(ds, {"
        '"metadata_type": "my_md",'
        '"name": "crazy_fork:latest",'
        '}), lambda e: e.crazy("fork").pT())'
    )

    exe = do_nothing_executor({"my_md": MyMD("t1", "t2")})
    _ = exe.apply_ast_transformations(a1)
    md = exe.extended_md("my_md")
    assert len(md) == 1
    assert md[0].name == "crazy_fork:latest"
