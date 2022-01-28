import ast
from func_adl_xAOD.atlas.xaod.query_ast_visitor import atlas_xaod_query_ast_visitor
from typing import Callable, List
from func_adl_xAOD.common.event_collections import EventCollectionSpecification, event_collection_coder, event_collection_container
from func_adl_xAOD.common.cpp_ast import CPPCodeValue
from func_adl_xAOD.common.cpp_types import method_type_info

from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.executor import executor


class dummy_event_collection_coder(event_collection_coder):
    def get_running_code(self, container_type: event_collection_container) -> List[str]:
        return [f'{container_type} result = dude;']


class do_nothing_executor(executor):
    def __init__(self):
        super().__init__([], 'stuff.sh', 'dude', {})

    def get_visitor_obj(self) -> query_ast_visitor:
        return atlas_xaod_query_ast_visitor()

    def build_collection_callback(self, metadata: EventCollectionSpecification) -> Callable[[ast.Call], ast.Call]:
        ecc = dummy_event_collection_coder()
        return lambda cd: ecc.get_collection(metadata, cd)


def parse_statement(st: str) -> ast.AST:
    'Returns the interior of a parsed python statement as ast'
    return ast.parse(st).body[0].value  # type: ignore


def test_metadata_method():
    'Make sure the metadata call is properly dealt with'

    a1 = parse_statement('Select(MetaData(ds, {'
                         '"metadata_type": "add_method_type_info", '
                         '"type_string": "my_namespace::obj", '
                         '"method_name": "pT", '
                         '"return_type": "int", '
                         '}), lambda e: e + 1)')
    a2 = parse_statement('Select(ds, lambda e: e + 1)')

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert ast.dump(a2) == ast.dump(new_a1)

    t = method_type_info('my_namespace::obj', 'pT')
    assert t is not None
    assert t.r_type.type == 'int'
    assert not t.r_type.is_a_pointer


def test_metadata_cpp_code():
    'Make sure the metadata from a C++ bit of code is correctly put into type system'

    a1 = parse_statement('Select(MetaData(ds, {'
                         '"metadata_type": "add_cpp_function",'
                         '"name": "MyDeltaR",'
                         '"include_files": ["TVector2.h", "math.h"],'
                         '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
                         '"code": ['
                         '   "auto d_eta = eta1 - eta2;",'
                         '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
                         '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
                         '],'
                         '"return_type": "double"'
                         '}), lambda e: MyDeltaR(1,2,3,4))')

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert 'CPPCodeValue' in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)


def test_metadata_cpp_code_capture():
    'Make sure we do not capture bad data (bug seen)'

    a1 = parse_statement('Select(MetaData(MetaData(ds, {'
                         '"metadata_type": "add_job_script",'
                         '"name": "apply_corrections",'
                         '"script": ["line1"],'
                         '"depends_on": [],'
                         '}),{'
                         '"metadata_type": "add_cpp_function",'
                         '"name": "MyDeltaR",'
                         '"include_files": ["TVector2.h", "math.h"],'
                         '"arguments": ["eta1", "phi1", "eta2", "phi2"],'
                         '"code": ['
                         '   "auto d_eta = eta1 - eta2;",'
                         '   "auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);",'
                         '   "auto result = (d_eta*d_eta + d_phi*d_phi);"'
                         '],'
                         '"return_type": "double"'
                         '}), lambda e: MyDeltaR(1,2,3,4))')

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert 'CPPCodeValue' in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)


def test_metadata_collection():
    'Make sure the metadata for a new collections goes all the way through'

    a1 = parse_statement('Select(MetaData(ds, {'
                         '"metadata_type": "add_atlas_event_collection_info",'
                         '"name": "crazy",'
                         '"include_files": ["xAODEventInfo/EventInfo.h"],'
                         '"container_type": "xAOD::EventInfo",'
                         '"contains_collection": True,'
                         '"element_type": "Fork",'
                         '}), lambda e: e.crazy("fork").pT())')

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert 'CPPCodeValue' in ast.dump(new_a1)

    call_obj = new_a1.args[1].body.func.value.func  # type: ignore
    assert isinstance(call_obj, CPPCodeValue)
    assert "dude" in "-".join(call_obj.running_code)


def test_include_files():
    'Make sure include files are properly dealt with'

    a1 = parse_statement('Select(MetaData(ds, {'
                         '"metadata_type": "inject_code",'
                         '"body_includes": ["xAODEventInfo/EventInfo.h"],'
                         '"header_includes": ["file.hpp"],'
                         '}), lambda e: e.crazy("fork").pT())')

    exe = do_nothing_executor()
    _ = exe.apply_ast_transformations(a1)
    assert exe.body_include_files == ["xAODEventInfo/EventInfo.h"]
    assert exe.header_include_files == ["file.hpp"]
