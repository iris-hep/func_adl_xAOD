import ast
from func_adl_xAOD.common.meta_data import generate_script_block
from func_adl_xAOD.atlas.xaod.event_collections import atlas_event_collection_coder, atlas_xaod_collections, define_default_atlas_types
from typing import Any, Callable, Dict
from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from func_adl_xAOD.common.math_utils import get_math_methods
from func_adl_xAOD.atlas.xaod.jets import get_jet_methods
from func_adl_xAOD.atlas.xaod.query_ast_visitor import \
    atlas_xaod_query_ast_visitor
from func_adl_xAOD.common.executor import executor


class atlas_xaod_executor(executor):
    def __init__(self):
        file_names = ['ATestRun_eljob.py', 'package_CMakeLists.txt', 'query.cxx', 'query.h', 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/atlas/r21'
        self._ecc = atlas_event_collection_coder()
        method_names: Dict[str, Callable[[ast.Call], ast.Call]] = {
            md.name: self.build_callback(self._ecc, md)
            for md in atlas_xaod_collections
        }
        method_names.update(get_jet_methods())
        method_names.update(get_math_methods())
        super().__init__(file_names, runner_name, template_dir_name, method_names)
        define_default_atlas_types()

    @staticmethod
    def build_callback(ecc, md):
        'Required due to by-reference lambda capture not working as expected in python'
        return lambda cd: ecc.get_collection(md, cd)

    def reset(self):
        '''Reset our atlas default types
        '''
        super().reset()
        define_default_atlas_types()

    def get_visitor_obj(self):
        return atlas_xaod_query_ast_visitor()

    def add_to_replacement_dict(self) -> Dict[str, Any]:
        d1 = super().add_to_replacement_dict()

        # Combine metadata script blocks
        d = {
            'job_option_additions': generate_script_block(self._job_option_blocks)
        }
        d.update(d1)
        return d

    def build_collection_callback(self, metadata: EventCollectionSpecification) -> Callable[[ast.Call], ast.Call]:
        '''Build the AST analyzer callback for this collection.

        Args:
            metadata (EventCollectionSpecification): The metadata describing this collection

        Returns:
            Callable[[ast.Call], ast.Call]: Function that will implement what is needed to build the ast properly.
        '''
        if metadata.backend_name != 'atlas':
            raise ValueError(f'Attempt to create a collection from metadata for the {metadata.backend_name} backend; only "atlas" allowed.')

        return lambda cd: self._ecc.get_collection(metadata, cd)
