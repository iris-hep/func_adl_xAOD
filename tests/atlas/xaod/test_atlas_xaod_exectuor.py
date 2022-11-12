import ast

import pytest
from func_adl.event_dataset import EventDataset
from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor


def test_ctor():
    "Make sure that the ctor works"
    atlas_xaod_executor()


class query_as_ast(EventDataset):
    async def execute_result_async(self, a: ast.AST, title: str):
        return a


def test_xaod_executor(tmp_path):
    "Write out C++ files for a simple query"

    # Get the ast to play with
    a = query_as_ast().Select(lambda e: e.EventInfo("EventInfo").runNumber()).value()

    exe = atlas_xaod_executor()
    f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)
    for name in f_spec.all_filenames:
        assert (tmp_path / name).exists()


def test_xaod_library_there(tmp_path):
    "Make sure a required library is in the link list"
    # Get the ast to play with
    a = query_as_ast().Select(lambda e: e.EventInfo("EventInfo").runNumber()).value()

    exe = atlas_xaod_executor()
    exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    make_list = tmp_path / "package_CMakeLists.txt"
    assert make_list.exists()
    assert "xAODEventInfo" in make_list.read_text()


def test_eventinfo_handle_code(tmp_path):
    "Make sure a required library is in the link list"
    # Get the ast to play with
    a = query_as_ast().Select(lambda e: e.EventInfo("EventInfo").runNumber()).value()

    exe = atlas_xaod_executor()
    exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    query = tmp_path / "query.cxx"
    assert "const xAOD::EventInfo *" in query.read_text()


def test_find_exception():
    "Make sure _find exception is well formed"
    from func_adl_xAOD.common.executor import _find

    with pytest.raises(RuntimeError) as e:
        _find("fork-it-over.txt")

    assert "find file" in str(e.value)


def test_bad_ast_no_call(tmp_path):
    "Pass a really bogus ast to the executor"
    # Get the ast to play with
    q = query_as_ast()
    a = ast.UnaryOp(op=ast.USub(), operand=q.query_ast)

    exe = atlas_xaod_executor()
    with pytest.raises(ValueError) as e:
        exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    assert "func_adl ast" in str(e.value)


def test_bad_ast_no_call_to_name(tmp_path):
    "Pass a really bogus ast to the executor"
    # Get the ast to play with
    q = query_as_ast()
    a = ast.Call(
        func=ast.Attribute(value=ast.Constant(10), attr="fork"), args=[q.query_ast]
    )

    exe = atlas_xaod_executor()
    with pytest.raises(ValueError) as e:
        exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    assert "func_adl ast" in str(e.value)


def test_md_job_options(tmp_path):
    "Make sure our job options script appears in the right place"

    # Get the ast to play with
    a = (
        query_as_ast()
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "Vertex",
                "script": [
                    "# this is a fork tester",
                ],
            }
        )
        .Select(lambda e: e.EventInfo("EventInfo").runNumber())
        .value()
    )

    exe = atlas_xaod_executor()
    exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    with open(tmp_path / "ATestRun_eljob.py", "r") as f:
        lines = [ln.strip() for ln in f.readlines()]
        assert "# this is a fork tester" in lines


def test_md_replaced_collection(tmp_path):
    "When we replace a collection, make sure all goes right"
    # Get the ast to play with
    a = (
        query_as_ast()
        .MetaData(
            {
                "metadata_type": "add_atlas_event_collection_info",
                "name": "EventInfo",
                "include_files": ["xAODEventInfo/versions/EventInfo_v1.h"],
                "container_type": "xAOD::EventInfo_v1",
                "contains_collection": False,
                "link_libraries": ["xAODEventInfo"],
            }
        )
        .Select(lambda e: e.EventInfo("EventInfo").runNumber())
        .value()
    )

    exe = atlas_xaod_executor()
    exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    query = tmp_path / "query.cxx"
    assert query.exists()
    assert "const xAOD::EventInfo_v1 *" in query.read_text()
