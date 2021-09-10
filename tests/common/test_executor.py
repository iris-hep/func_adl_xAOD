import ast
from func_adl_xAOD.common.cpp_types import method_type_info

from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.executor import executor


class do_nothing_executor(executor):
    def __init__(self):
        super().__init__([], 'stuff.sh', 'dude', {})

    def get_visitor_obj(self) -> query_ast_visitor:
        assert False


def parse_statement(st: str) -> ast.AST:
    'Returns the interior of a parsed python statement as ast'
    return ast.parse(st).body[0].value  # type: ignore


def test_metadata_dealt_with():
    'Make sure the metadata call is properly dealt with'

    a1 = parse_statement('Select(MetaData(ds, {'
                         '"metadata_type": "add_method_type_info", '
                         '"type_string": "my_namespace::obj", '
                         '"method_name": "pT", '
                         '"return_type": "int", '
                         '"is_pointer": "False", '
                         '}), lambda e: e + 1)')
    a2 = parse_statement('Select(ds, lambda e: e + 1)')

    new_a1 = do_nothing_executor().apply_ast_transformations(a1)

    assert ast.dump(a2) == ast.dump(new_a1)

    t = method_type_info('my_namespace::obj', 'pT')
    assert t is not None
    assert t.type == 'int'
    assert t.is_pointer() is False
