# Collected code to get collections from the event object
import ast
import copy

from abc import ABC, abstractmethod

import func_adl_xAOD.common_lib.cpp_ast as cpp_ast
import func_adl_xAOD.common_lib.cpp_representation as crep
import func_adl_xAOD.common_lib.cpp_types as ctyp

from func_adl_xAOD.common_lib.cpp_vars import unique_name


# Need a type for our type system to reason about the containers.
class event_collection_container(ABC):
    def __init__(self, type_name, is_pointer=True):
        self._type_name = type_name
        self._is_pointer = is_pointer

    def is_pointer(self):
        return self._is_pointer

    @abstractmethod
    def __str__(self):
        pass


class event_collection_collection(event_collection_container):
    def __init__(self, type_name, element_name):
        event_collection_container.__init__(self, type_name)
        self._element_name = element_name

    def element_type(self):
        'Return the type of the elements in the collection'
        return ctyp.terminal(self._element_name, is_pointer=True)

    def dereference(self):
        'Return a new version of us that is not a pointer'
        new_us = copy.copy(self)
        new_us._is_pointer = False
        return new_us


def getCollection(info, call_node):
    r'''
    Return a cpp ast for accessing the jet collection
    '''
    # Get the name jet collection to look at.
    if len(call_node.args) != 1:
        raise ValueError(f"Calling {info['function_name']} - only one argument is allowed")
    if not isinstance(call_node.args[0], ast.Str):
        raise ValueError(f"Calling {info['function_name']} - only acceptable argument is a string")

    # Fill in the CPP block next.
    r = cpp_ast.CPPCodeValue()
    r.args = ['collection_name', ]
    r.include_files += info['include_files']

    r.running_code += ['{0} result = 0;'.format(info['container_type']),
                       'ANA_CHECK (evtStore()->retrieve(result, collection_name));']
    r.result = 'result'

    is_collection = info['is_collection'] if 'is_collection' in info else True
    if is_collection:
        r.result_rep = lambda scope: crep.cpp_collection(unique_name(info['function_name'].lower()), scope=scope, collection_type=info['container_type'])  # type: ignore
    else:
        r.result_rep = lambda scope: crep.cpp_variable(unique_name(info['function_name'].lower()), scope=scope, cpp_type=info['container_type'])

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node


# Config everything.
def create_higher_order_function(info):
    'Creates a higher-order function because python scoping is broken'
    return lambda call_node: getCollection(info, call_node)