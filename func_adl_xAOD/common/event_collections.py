# Collected code to get collections from the event object
import ast
from collections import namedtuple
import copy
from abc import ABC, abstractmethod
from typing import List

import func_adl_xAOD.common.cpp_ast as cpp_ast
import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.cpp_vars import unique_name


EventCollectionSpecification = namedtuple('EventCollectionSpecification', ['backend_name', 'name', 'include_files', 'container_type'])


# Need a type for our type system to reason about the containers.
class event_collection_container(ABC):
    def __init__(self, type_name, is_pointer):
        self._type_name = type_name
        self._is_pointer = is_pointer

    def is_pointer(self):
        return self._is_pointer

    @abstractmethod
    def __str__(self):
        pass


class event_collection_collection(event_collection_container):
    def __init__(self, type_name, element_name, is_type_pointer, is_element_pointer):
        event_collection_container.__init__(self, type_name, is_type_pointer)
        self._element_name = element_name
        self._is_element_pointer = is_element_pointer

    def element_type(self):
        return ctyp.terminal(self._element_name, is_pointer=self._is_element_pointer)

    def dereference(self):
        'Return a new version of us that is not a pointer'
        new_us = copy.copy(self)
        new_us._is_pointer = False
        return new_us


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

        r.running_code += self.get_running_code(md.container_type)
        r.result = 'result'

        if issubclass(type(md.container_type), event_collection_collection):
            r.result_rep = lambda scope: crep.cpp_collection(unique_name(md.name.lower()), scope=scope, collection_type=md.container_type)  # type: ignore
        else:
            r.result_rep = lambda scope: crep.cpp_variable(unique_name(md.name.lower()), scope=scope, cpp_type=md.container_type)

        # Replace it as the function that is going to get called.
        call_node.func = r  # type: ignore

        return call_node

    @abstractmethod
    def get_running_code(self, container_type: event_collection_container) -> List[str]:
        '''Return the code that will extract the collection from the event object

        Args:
            container_type (event_collection_container): The container to extract.

        Returns:
            List[str]: Lines of C++ code to execute to get this out.
        '''
        pass
