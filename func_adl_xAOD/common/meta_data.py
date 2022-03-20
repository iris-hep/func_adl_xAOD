from func_adl_xAOD.common.event_collections import EventCollectionSpecification
from func_adl_xAOD.common.cpp_ast import CPPCodeSpecification
from func_adl_xAOD.common.cpp_types import add_method_type_info, collection, terminal
from func_adl_xAOD.common.cpp_types import CPPParsedTypeInfo, parse_type
from typing import Any, Dict, List, Union
from dataclasses import dataclass, field


@dataclass
class JobScriptSpecification:
    name: str
    script: List[str]
    depends_on: List[str]


@dataclass
class InjectCodeBlock:
    'Code to be directly injected into the hpp and cpp files'

    # Name of the code block
    name: str

    # Include files for the cpp code
    body_includes: List[str] = field(default_factory=list)

    # Include files for the hpp code
    header_includes: List[str] = field(default_factory=list)

    # Instance variable declarations
    private_members: List[str] = field(default_factory=list)

    # Instance variable ctor initializers
    instance_initialization: List[str] = field(default_factory=list)

    # Code lines to place in the constructor
    ctor_lines: List[str] = field(default_factory=list)

    # Lines to add to initialize statement
    initialize_lines: List[str] = field(default_factory=list)

    # Packages/Libraries to add to the CMake lib line
    link_libraries: List[str] = field(default_factory=list)


SpecificationTypes = Union[CPPCodeSpecification, EventCollectionSpecification, JobScriptSpecification, InjectCodeBlock]


def ok_to_add_code_block(spec, cpp_funcs: List[SpecificationTypes]) -> bool:
    '''Check already added code blocks specs to see if there is one with the same name,
    and if so, if its contents are the same.

    Return ok if this is a unique code block
    Return false if this is a duplicate
    Throw an error if the name but not content matches.

    Args:
        spec (InjectCodeBlock): The block to be going after
        cpp_funcs ([type]): The list code blocks we should find a match in
    '''
    for b in cpp_funcs:
        if isinstance(b, InjectCodeBlock) and b.name == spec.name:
            if b == spec:
                return False
            raise ValueError(f'Duplicate inject_code blocks with name {spec.name} that are not identical. Do not know which one to use! first: {b} second: {spec}')
    return True


def process_metadata(md_list: List[Dict[str, Any]]) -> List[SpecificationTypes]:
    '''Process a list of metadata, in order.

    Args:
        md (List[Dict[str, str]]): The metadata to process

    Returns:
        List[X]: Metadata we've found
    '''
    cpp_funcs: List[SpecificationTypes] = []
    for md in md_list:
        md_type = md.get('metadata_type')
        if md_type is None:
            raise ValueError(f'Metadata is missing `metadata_type` info ({md})')

        if md_type == 'add_method_type_info':
            if 'return_type' in md:
                # Single return type
                type_info = parse_type(md['return_type'])
                term = terminal(type_info.name, p_depth=type_info.pointer_depth)
            else:
                type_info_element = parse_type(md['return_type_element'])
                type_info_collection = parse_type(md['return_type_collection']) if 'return_type_collection' in md else CPPParsedTypeInfo(f'std::vector<{type_info_element}>', 0)
                term = collection(terminal(type_info_element), array_type=type_info_collection)
            d_count = 0
            if 'deref_count' in md:
                d_count = int(md['deref_count'])
            add_method_type_info(md['type_string'], md['method_name'], term, d_count)
        elif md_type == 'inject_code':
            info = dict(md)
            del info['metadata_type']
            if len(info) > 0:
                try:
                    spec = InjectCodeBlock(**info)
                except TypeError as e:
                    raise ValueError(f'Bad inject_code block item: {str(e)}')
                if ok_to_add_code_block(spec, cpp_funcs):
                    cpp_funcs.append(spec)
        elif md_type == 'add_job_script':
            spec = JobScriptSpecification(
                name=md['name'],
                script=md['script'],
                depends_on=md.get('depends_on', [])
            )
            cpp_funcs.append(spec)
        elif md_type == 'add_cpp_function':
            spec = CPPCodeSpecification(
                md['name'],
                md['include_files'],
                md['arguments'],
                md['code'],
                md['result_name'] if 'result_name' in md else 'result',
                md['return_type'],
                bool(md['return_is_collection']) if 'return_is_collection' in md else False,
                md['method_object'] if 'method_object' in md else None,
                md['instance_object'] if 'instance_object' in md else None,
            )
            cpp_funcs.append(spec)
        elif md_type == 'add_atlas_event_collection_info':
            for k in md.keys():
                if k not in ['metadata_type', 'name', 'include_files', 'container_type', 'element_type', 'contains_collection', 'link_libraries']:
                    raise ValueError(f'Unexpected key {k} when declaring ATLAS collection metadata')
            if (md['contains_collection'] and 'element_type' not in md) or (not md['contains_collection'] and 'element_type' in md):
                raise ValueError('In collection metadata, `element_type` must be specified if `contains_collection` is true and not if it is false')

            from func_adl_xAOD.atlas.xaod.event_collections import atlas_xaod_event_collection_collection, atlas_xaod_event_collection_container
            container_type = atlas_xaod_event_collection_collection(md['container_type'], md['element_type']) if md['contains_collection'] \
                else atlas_xaod_event_collection_container(md['container_type'])
            link_libraries = [] if 'link_libraries' not in md else md['link_libraries']
            spec = EventCollectionSpecification(
                'atlas',
                md['name'],
                md['include_files'],
                container_type,
                link_libraries)
            cpp_funcs.append(spec)
        elif md_type == 'add_cms_event_collection_info':
            for k in md.keys():
                if k not in ['metadata_type', 'name', 'include_files', 'container_type', 'element_type', 'contains_collection', 'element_pointer']:
                    raise ValueError(f'Unexpected key {k} when declaring ATLAS collection metadata')
            if (md['contains_collection'] and 'element_type' not in md) or (not md['contains_collection'] and 'element_type' in md):
                raise ValueError('In collection metadata, `element_type` must be specified if `contains_collection` is true and not if it is false')

            from func_adl_xAOD.cms.aod.event_collections import cms_aod_event_collection_collection
            container_type = cms_aod_event_collection_collection(md['container_type'], md['element_type'])
            # container_type = cms_aod_event_collection_collection(md['container_type'], md['element_type']) if md['contains_collection'] \
            #     else cms_aod_event_collection_container(md['container_type'])

            spec = EventCollectionSpecification(
                'cms',
                md['name'],
                md['include_files'],
                container_type,
                [])
            cpp_funcs.append(spec)
        else:
            raise ValueError(f'Unknown metadata type ({md_type})')

    return cpp_funcs


def generate_script_block(blocks: List[JobScriptSpecification]) -> List[str]:
    '''Returns the script block to insert into the job control.

    * Takes dependencies into account
    * Gets rid of any duplicates
    * Will combine any blocks with the same script text, but different dependencies.

    Args:
        blocks (List[JobScriptSpecification]): The list of, unordered, dependency blocks

    Returns:
        List[str]: The list of insertions to insert.
    '''
    # Build the dependency graph and check for improper
    # duplications and dependencies.
    dependencies: Dict[str, List[str]] = {}
    block_lookup: Dict[str, JobScriptSpecification] = {}

    for b in blocks:
        if b.name not in dependencies:
            dependencies[b.name] = []
            block_lookup[b.name] = b
        else:
            if b.script != block_lookup[b.name].script:
                raise ValueError(f'Duplicate metadata block "{b.name}", but blocks are not identical ({b.script} and {block_lookup[b.name].script} should be identical)!')

        dependencies[b.name].extend(b.depends_on)

    for name, deps in dependencies.items():
        for d in deps:
            if d not in dependencies:
                raise ValueError(f'Dependent metadata block {d} not found in sent metadata (from {name}!')

    # Next, start from blocks that have no dependencies and work our way up.
    seen_blocks = set()
    script_text = []

    while len(seen_blocks) < len(dependencies):
        emitted = False
        for j in block_lookup.values():
            if j.name not in seen_blocks:
                if set(dependencies[j.name]) <= seen_blocks:
                    for ln in j.script:
                        script_text.append(ln)
                    seen_blocks.add(j.name)
                    emitted = True
        if not emitted:
            remaining_blocks = ', '.join((set(block_lookup.keys()) - seen_blocks))
            raise ValueError(f'There seems to be a metadata script block circular dependency ({remaining_blocks})')

    return script_text
