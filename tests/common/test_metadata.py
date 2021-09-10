from typing import List
from func_adl_xAOD.common.event_collections import event_collection_container, event_collections
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from tests.utils.base import dataset, dummy_executor  # type: ignore
import func_adl_xAOD.common.statement as statement


# We need to setup a whole dummy dataset so we can test this in isolation of CMS and ATLAS
# code.
class my_event_collection_container(event_collection_container):
    def __init__(self, obj_name: str):
        super().__init__(obj_name, True)

    def __str__(self):
        return 'my_namespace::obj'


dummy_collections = [
    {
        'function_name': "info",
        'include_files': ['xAODEventInfo/EventInfo.h'],
        'container_type': my_event_collection_container('base_cpp:info_object'),
        'is_collection': False,
    }
]


class dummy_event_collections(event_collections):
    def __init__(self):
        super().__init__(dummy_collections)

    def get_running_code(self, container_type: event_collection_container) -> List[str]:
        return [f'{container_type} result;']


class dummy_book_ttree(statement.book_ttree):
    def __init__(self):
        super().__init__('hi', ['one', 'two'])

    def emit(self, e):
        pass


class dummy_ttree_fill(statement.ttree_fill):
    def __init__(self):
        super().__init__('hi')

    def emit(self, e):
        pass


class dummy_query_ast_visitor(query_ast_visitor):
    def __init__(self):
        super().__init__('dummy', False)

    def create_book_ttree_obj(self, tree_name: str, leaves: list) -> statement.book_ttree:
        return dummy_book_ttree()

    def create_ttree_fill_obj(self, tree_name: str) -> statement.ttree_fill:
        return dummy_ttree_fill()


class my_executor(executor):
    def __init__(self):
        method_names = dummy_event_collections().get_method_names()
        super().__init__([], 'dummy.sh', 'dude/shark', method_names)

    def get_visitor_obj(self) -> query_ast_visitor:
        return dummy_query_ast_visitor()


class my_dummy_executor(dummy_executor):
    'A dummy executor that will return basic ast visiting'
    def __init__(self):
        super().__init__()

    def get_executor_obj(self):
        return my_executor()

    def get_visitor_obj(self):
        return dummy_query_ast_visitor()


class my_dataset(dataset):
    'A dummy dataset to base func_adl queries on'
    def __init__(self):
        super().__init__()

    def get_dummy_executor_obj(self) -> dummy_executor:
        return my_dummy_executor()


def test_no_type_info_warning(caplog):
    'Call a function that is "ok" but has no type info'
    (my_dataset()
        .Select(lambda e: e.info('fork').pT())
        .value()
     )

    assert 'pT' in caplog.text


def test_with_type(caplog):
    'Call a function that is "ok" and has type info declared in metadata'

    # import func_adl_xAOD.common.cpp_types as ctyp
    # ctyp.add_method_type_info('my_namespace::obj', 'pT', ctyp.terminal('int'))

    (my_dataset()
        .MetaData({
            'metadata_type': 'add_method_type_info',
            'type_string': 'my_namespace::obj',
            'method_name': 'pT',
            'return_type': 'int',
            'is_pointer': 'False',
        })
        .Select(lambda e: e.info('fork').pT())
        .value()
     )

    assert 'pT' not in caplog.text
