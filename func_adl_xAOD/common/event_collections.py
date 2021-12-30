# Collected code to get collections from the event object
import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union

import func_adl_xAOD.common.cpp_ast as cpp_ast
import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.cpp_vars import unique_name


class event_collection_container(ctyp.terminal, ABC):
    def __init__(self, type_name: Union[str, ctyp.CPPParsedTypeInfo], p_depth: int):
        super().__init__(type_name, p_depth=p_depth)

    @abstractmethod
    def __str__(self) -> str:
        '''Return the string representation of this event collection.
        Helpful for identifying it in ast dumps

        Returns:
            str: Description
        '''


class event_collection_collection_container(ctyp.collection, ABC):
    def __init__(self, type_name: Union[str, ctyp.CPPParsedTypeInfo],
                 element_name: Union[str, ctyp.CPPParsedTypeInfo],
                 p_depth_type: int, p_depth_element: int):
        super().__init__(
            ctyp.terminal(element_name, p_depth=p_depth_element),
            array_type=type_name, p_depth=p_depth_type
        )

    @abstractmethod
    def __str__(self) -> str:
        '''Return the string representation of this event collection.
        Helpful for identifying it in ast dumps

        Returns:
            str: Description
        '''


@dataclass
class EventCollectionSpecification:
    backend_name: str
    name: str

    # List of include files (e.g. ['xAODJet/Jet.h'])
    include_files: List[str]

    # The container information
    container_type: Union[event_collection_container, event_collection_collection_container]

    # List of libraries (e.g. ['xAODJet'])
    libraries: List[str]


class event_collection_coder(ABC):
    '''Contains code to generate collections accessing code in the backend
    '''
    def get_collection(self, md: EventCollectionSpecification, call_node: ast.Call):
        r'''
        Return a cpp ast for accessing the jet collection with the given arguments.
        '''
        # Get the name jet collection to look at.
        if len(call_node.args) != 1:
            raise ValueError(f"Calling {md.name} - only one argument is allowed")
        if not isinstance(call_node.args[0], ast.Str):
            raise ValueError(f"Calling {md.name} - only acceptable argument is a string")

        # Fill in the CPP block next.
        r = cpp_ast.CPPCodeValue()
        r.args = ['collection_name', ]
        r.include_files += md.include_files
        r.link_libraries += md.libraries

        r.running_code += self.get_running_code(md.container_type)
        r.result = 'result'

        if issubclass(type(md.container_type), event_collection_collection_container):
            r.result_rep = lambda scope: crep.cpp_collection(unique_name(md.name.lower()), scope=scope, collection_type=md.container_type)  # type: ignore
        else:
            r.result_rep = lambda scope: crep.cpp_variable(unique_name(md.name.lower()), scope=scope, cpp_type=md.container_type)

        # Replace it as the function that is going to get called.
        call_node.func = r  # type: ignore

        return call_node

    @abstractmethod
    def get_running_code(self, container_type: Union[event_collection_container, event_collection_collection_container]) -> List[str]:
        '''Return the code that will extract the collection from the event object

        Args:
            container_type (event_collection_container): The container to extract.

        Returns:
            List[str]: Lines of C++ code to execute to get this out.
        '''
