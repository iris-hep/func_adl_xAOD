
from func_adl_xAOD.common.cpp_ast import CPPCodeSpecification
from func_adl_xAOD.common.cpp_types import add_method_type_info, terminal
from typing import Dict, List


def process_metadata(md_list: List[Dict[str, str]]) -> List[CPPCodeSpecification]:
    '''Process a list of metadata, in order.

    Args:
        md (List[Dict[str, str]]): The metadata to process

    Returns:
        List[CPPCodeSpecification]: Any C++ functions that were defined in the metadata
    '''
    cpp_funcs = []
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
                md['return_type']
            )
            cpp_funcs.append(spec)
        else:
            raise ValueError(f'Unknown metadata type ({md_type})')

    return cpp_funcs
