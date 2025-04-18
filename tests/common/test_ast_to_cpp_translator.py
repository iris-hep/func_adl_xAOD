import ast
from typing import Callable

from func_adl import ObjectStream
from pandas.tests.api import test_types

import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.ast_to_cpp_translator import (
    find_fill_scope,
    query_ast_visitor,
)
from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.util_scope import top_level_scope
from tests.utils.base import dataset, dummy_executor


class my_executor(executor):

    def execute(self):
        pass

    def get_visitor_obj(self) -> query_ast_visitor:
        raise NotImplementedError()

    def build_collection_callback(
        self, metadata: EventCollectionSpecification
    ) -> Callable[[ast.Call], ast.Call]:
        raise NotImplementedError()


class dummy_dataset(dataset):
    def __init__(self, qastle_roundtrip=False):
        super().__init__(qastle_roundtrip=qastle_roundtrip)

    def get_dummy_executor_obj(self) -> dummy_executor:
        raise NotImplementedError()


def get_ast(r: ObjectStream, t="int", is_collection: bool = False) -> ast.AST:

    from func_adl import find_EventDataset

    t_type = ctyp.terminal(ctyp.parse_type(t))
    iterator = crep.cpp_variable(
        "bogus-do-not-use",
        top_level_scope(),
        cpp_type=t_type,
    )
    if is_collection:
        t_type = ctyp.collection(t_type)
        iterator = crep.cpp_collection(
            "bogus-do-not-use-array", top_level_scope(), t_type
        )

    file = find_EventDataset(r.query_ast)
    crep.set_rep(file, crep.cpp_sequence(iterator, iterator, top_level_scope(), file))

    return my_executor([], "my_runner", "template_name", {}).apply_ast_transformations(
        r.query_ast
    )


class our_ast_visitor(query_ast_visitor):
    def create_ttree_fill_obj(self, tree_name: str):
        raise NotImplementedError()

    def create_book_ttree_obj(self, tree_name: str, leaves: list):
        raise NotImplementedError()


def test_iterator():
    "Simple expression"

    r_ast = get_ast(dummy_dataset())

    # Parse the top.
    parser = our_ast_visitor("dork")
    r = parser.get_rep(r_ast)

    # The only iterator is the dummy overall event one we create!
    assert isinstance(r, crep.cpp_sequence)
    assert r.iterator_value().as_cpp() == "bogus-do-not-use"
    assert r.sequence_value().as_cpp() == "bogus-do-not-use"
    assert r.sequence_value().cpp_type().type == "int"

    # Check the scopes
    assert r.iterator_value().scope().is_top_level()
    assert r.scope().is_top_level()


def test_iterator_with_where():
    "Simple expression"

    r_ast = get_ast(dummy_dataset().Where(lambda e: e > 10))

    # Parse the top.
    parser = our_ast_visitor("dork")
    r = parser.get_rep(r_ast)

    # The only iterator is the dummy overall event one we create!
    assert isinstance(r, crep.cpp_sequence)
    assert r.iterator_value().as_cpp() == "bogus-do-not-use"
    assert r.sequence_value().as_cpp() == "bogus-do-not-use"
    assert r.sequence_value().cpp_type().type == "int"

    # Check the scopes
    assert r.iterator_value().scope().is_top_level()
    assert not r.scope().is_top_level()


def test_iterator_with_select():
    "Simple expression"

    r_ast = get_ast(dummy_dataset().Select(lambda e: e + 1))

    # Parse the top.
    parser = our_ast_visitor("dork")
    r = parser.get_rep(r_ast)

    # The only iterator is the dummy overall event one we create!
    assert isinstance(r, crep.cpp_sequence)
    assert r.iterator_value().as_cpp() == "bogus-do-not-use"
    assert r.sequence_value().as_cpp() == "(bogus-do-not-use+1)"
    assert r.sequence_value().cpp_type().type == "int"

    # Check the scopes
    assert r.iterator_value().scope().is_top_level()


def test_iterator_with_select_sequence_len():
    "Simple expression"

    r_ast = get_ast(dummy_dataset().Select(lambda e: len(e)), "int", is_collection=True)

    # Parse the top.
    parser = our_ast_visitor("dork")
    r = parser.get_rep(r_ast)

    # The only iterator is the dummy overall event one we create!
    assert isinstance(r, crep.cpp_sequence)
    assert r.iterator_value().as_cpp() == "bogus-do-not-use-array"
    assert r.sequence_value().cpp_type().type == "int"

    # Check the scopes
    assert r.iterator_value().scope().is_top_level()


def test_iterator_with_select_sequence():
    "Simple expression"

    r_ast = get_ast(
        dummy_dataset().Select(lambda e: e.Select(lambda v: v + 1)),
        "int",
        is_collection=True,
    )

    # Parse the top.
    parser = our_ast_visitor("dork")
    r = parser.get_rep(r_ast)

    # The only iterator is the dummy overall event one we create!
    assert isinstance(r, crep.cpp_sequence)
    assert r.iterator_value().as_cpp() == "bogus-do-not-use-array"
    assert r.sequence_value().cpp_type().type == "std::vector<int>"

    # Check the scopes
    assert r.iterator_value().scope().is_top_level()
    # This should be the scope of the iterator, which is inside that
    # second loop!
    assert not r.scope().is_top_level()


def extract_call_name(a: ast.AST) -> str:
    """Extract the name of the call from the AST."""
    assert isinstance(a, ast.Call)
    assert isinstance(a.func, ast.Name)
    return a.func.id


def test_fill_scope_dataset():
    r_ast = get_ast(dummy_dataset())

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "EventDataset"


def test_fill_scope_with_select():
    r_ast = get_ast(dummy_dataset().Select(lambda v: v + 1))

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "EventDataset"


def test_fill_scope_with_where():
    r_ast = get_ast(dummy_dataset().Where(lambda v: v > 10).Select(lambda v: v + 1))

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "Where"


def test_fill_scope_with_where_with_distractions():
    r_ast = get_ast(
        dummy_dataset()
        .Where(lambda v_list: len(v_list) > 10)
        .Select(lambda v_list: v_list.Where(lambda v: v > 5)),
        is_collection=True,
    )

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "Where"
    assert ast.unparse(r).endswith("> 10)")


def test_fill_scope_with_where_in_distractions_only():
    r_ast = get_ast(
        dummy_dataset()
        .Select(lambda v_list: v_list.Where(lambda v: v > 5))
        .Select(lambda v_list: v_list.Where(lambda v: v > 10)),
        is_collection=True,
    )

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "EventDataset"


def test_fill_scope_SelectMany():
    r_ast = get_ast(
        dummy_dataset().SelectMany(lambda v_list: v_list),
        is_collection=True,
    )

    r = find_fill_scope(r_ast)
    assert extract_call_name(r) == "SelectMany"
