import string
from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.statement import book_ttree, set_var, ttree_fill
from func_adl_xAOD.common.util_scope import gc_scope_top_level
import func_adl_xAOD.common.cpp_types as ctyp
import func_adl_xAOD.common.cpp_representation as crep
from func_adl_xAOD.common.event_collections import EventCollectionSpecification
class book_cms_miniaod_ttree(book_ttree):
    'Book an CMS TTree for writing out. Meant to be in the Book method'

    def __init__(self, tree_name, leaves):
        super().__init__(tree_name, leaves)

    def emit(self, e):
        'Emit the book statement for a tree'
        e.add_line("edm::Service<TFileService> fs;")
        e.add_line('myTree = fs->make<TTree>("{0}", "My analysis ntuple");'.format(
            self._tree_name))
        for var_pair in self._leaves:
            e.add_line('myTree->Branch("{0}", &{1});'.format(var_pair[0], var_pair[1].as_cpp()))


class cms_miniaod_ttree_fill(ttree_fill):
    'Fill a CMS TTree'

    def __init__(self, tree_name):
        super().__init__(tree_name)

    def emit(self, e):
        e.add_line('myTree->Fill();')

# class cms_miniaod_initialize_token(set_var):
#     'for initializing the token'

#     def __init__(self, target_var, value_var):
#         super().__init__(target_var, value_var)


class cms_miniaod_query_ast_visitor(query_ast_visitor):
    r"""
    Drive the conversion to C++ from the top level query
    for CMS miniAOD
    """

    def __init__(self):
        prefix = 'cms_miniaod'
        super().__init__(prefix)

    def create_book_ttree_obj(self, tree_name: str, leaves: list) -> book_ttree:
        return book_cms_miniaod_ttree(tree_name, leaves)

    def create_ttree_fill_obj(self, tree_name: str) -> ttree_fill:
        return cms_miniaod_ttree_fill(tree_name)
