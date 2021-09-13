from func_adl_xAOD.cms.aod.event_collections import cms_aod_event_collection_collection, cms_aod_event_collection_container
from func_adl_xAOD.atlas.xaod.event_collections import atlas_xaod_event_collection_collection, atlas_xaod_event_collection_container
from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from func_adl_xAOD.common.cpp_ast import CPPCodeSpecification
from func_adl_xAOD.common.cpp_types import add_method_type_info, terminal
from typing import Dict, List, Union


def process_metadata(md_list: List[Dict[str, str]]) -> List[Union[CPPCodeSpecification, EventCollectionSpecification]]:
    '''Process a list of metadata, in order.

    Args:
        md (List[Dict[str, str]]): The metadata to process

    Returns:
        List[CPPCodeSpecification]: Any C++ functions that were defined in the metadata
    '''
    cpp_funcs: List[Union[CPPCodeSpecification, EventCollectionSpecification]] = []
    for md in md_list:
        md_type = md.get('metadata_type')
        if md_type is None:
            raise ValueError(f'Metadata is missing `metadata_type` info ({md})')

        if md_type == 'add_method_type_info':
            add_method_type_info(md['type_string'], md['method_name'], terminal(md['return_type'], is_pointer=md['is_pointer'].upper() == 'TRUE'))
        elif md_type == 'add_cpp_function':
            spec = CPPCodeSpecification(
                md['name'],
                md['include_files'],
                md['arguments'],
                md['code'],
                md['result_name'] if 'result_name' in md else 'result',
                md['return_type'],
            )
            cpp_funcs.append(spec)
        elif md_type == 'add_atlas_event_collection_info':
            for k in md.keys():
                if k not in ['metadata_type', 'name', 'include_files', 'container_type', 'element_type', 'contains_collection']:
                    raise ValueError(f'Unexpected key {k} when declaring ATLAS collection metadata')
            if (md['contains_collection'] and 'element_type' not in md) or (not md['contains_collection'] and 'element_type' in md):
                raise ValueError('In collection metadata, `element_type` must be specified if `contains_collection` is true and not if it is false')

            container_type = atlas_xaod_event_collection_collection(md['container_type'], md['element_type']) if md['contains_collection'] \
                else atlas_xaod_event_collection_container(md['container_type'])
            spec = EventCollectionSpecification(
                'atlas',
                md['name'],
                md['include_files'],
                container_type)
            cpp_funcs.append(spec)
        elif md_type == 'add_cms_event_collection_info':
            for k in md.keys():
                if k not in ['metadata_type', 'name', 'include_files', 'container_type', 'element_type', 'contains_collection', 'element_pointer']:
                    raise ValueError(f'Unexpected key {k} when declaring ATLAS collection metadata')
            if (md['contains_collection'] and 'element_type' not in md) or (not md['contains_collection'] and 'element_type' in md):
                raise ValueError('In collection metadata, `element_type` must be specified if `contains_collection` is true and not if it is false')

            container_type = cms_aod_event_collection_collection(md['container_type'], md['element_type']) if md['contains_collection'] \
                else cms_aod_event_collection_container(md['container_type'])

            spec = EventCollectionSpecification(
                'cms',
                md['name'],
                md['include_files'],
                container_type)
            cpp_funcs.append(spec)
        else:
            raise ValueError(f'Unknown metadata type ({md_type})')

    return cpp_funcs
