# Simple type system to help reason about types as they go through the system.


from typing import Optional


class terminal:
    'Represents something we cannot see inside, like float, or int, or bool'

    def __init__(self, t: str, is_pointer: bool = False):
        '''Create a terminal type - a type that we do not need to see inside

        Args:
            t (str): The name of the type (integer, double, xAOD::Jet, etc.)
            is_pointer (bool, optional): True if this is a pointer. Defaults to False.
        '''
        self._type = t
        self._is_pointer = is_pointer

    def __str__(self):
        return str(self.type)

    def is_pointer(self):
        return self._is_pointer

    def default_value(self):
        raise NotImplementedError()
        # if self._type == "double":
        #     return "0.0"
        # elif self._type == "float":
        #     return "0.0"
        # elif self._type == "int":
        #     return "0"
        # else:
        #     raise Exception(f"Do not know a default value for the type '{self._type}'.")

    @property
    def type(self) -> str:
        return self._type

    def get_dereferenced_type(self):
        return terminal(self._type, is_pointer=False) if self._is_pointer else self


class collection (terminal):
    'Represents a collection/list/vector of the same type'

    def __init__(self, t, is_pointer: bool = False, array_type: Optional[str] = None):
        '''
        Initialize a collection type.

        t:          The type of each element in the collection
        is_pointer: True if this is a pointer. Defaults to False.
        array_type: The type of the array. Defaults to None, in which case
                    vector<t> is used.
        '''
        if array_type is None:
            array_type = f"std::vector<{t}>"
        super().__init__(array_type, is_pointer)

        self._element_type = t

    def element_type(self):
        return self._element_type


###########################
# Manage types


g_method_type_dict = {}


def add_method_type_info(type_string: str, method_name: str, t: terminal):
    '''
    Define a return type for a method

    type_string         String of the object the method is calling against
    method_name         Name of the object
    t                   The type (terminal, collection, etc.) of return type
    '''
    if type_string not in g_method_type_dict:
        g_method_type_dict[type_string] = {}
    g_method_type_dict[type_string][method_name] = t


def method_type_info(type_string, method_name) -> Optional[terminal]:
    '''
    Return the type of the method's return value
    '''
    if type_string not in g_method_type_dict:
        return None
    if method_name not in g_method_type_dict[type_string]:
        return None
    return g_method_type_dict[type_string][method_name]
