import ast
from typing import Callable

from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.math_utils import get_math_methods

from .cms_functions import get_cms_functions
from .event_collections import (cms_aod_collections,
                                cms_event_collection_coder,
                                define_default_cms_types)
from .query_ast_visitor import cms_aod_query_ast_visitor


class cms_aod_executor(executor):
    def __init__(self):
        file_names = ['analyzer_cfg.py', 'Analyzer.cc', 'BuildFile.xml', "copy_root_tree.C", 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/cms/r5'

        self._ecc = cms_event_collection_coder()
        method_names = {
            md.name: self.build_callback(self._ecc, md)
            for md in cms_aod_collections
        }
        method_names.update(get_math_methods())
        method_names.update(get_cms_functions())

        super().__init__(file_names, runner_name, template_dir_name, method_names)

        define_default_cms_types()

    def reset(self):
        '''Reset system to initial state
        '''
        super().reset()
        define_default_cms_types()

    @staticmethod
    def build_callback(ecc, md):
        'Required due to by-reference lambda capture not working as expected in python'
        return lambda cd: ecc.get_collection(md, cd)

    def get_visitor_obj(self):
        return cms_aod_query_ast_visitor()

    def build_collection_callback(self, metadata: EventCollectionSpecification) -> Callable[[ast.Call], ast.Call]:
        if metadata.backend_name != 'cms':
            raise ValueError(f'Attempt to create a collection from metadata for the {metadata.backend_name} backend; only "atlas" allowed.')

        return lambda cd: self._ecc.get_collection(metadata, cd)
