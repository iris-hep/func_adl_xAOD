from typing import Dict, List
from dataclasses import dataclass

import func_adl_xAOD.common.cpp_types as ctyp

_type_priority: Dict[str, int] = {
    'int': 0,
    'float': 1,
    'double': 2,
}


def most_accurate_type(type_list: List[ctyp.terminal]) -> ctyp.terminal:
    '''
    Return the best type we can for most accurate sum. So if one is floating or double, return that.

    We only deal with terminals we know about.
    '''
    assert len(type_list) > 0, 'Internal error - looking for best types in null list'
    assert all(t.type in _type_priority for t in type_list), \
        f'Not all types ({", ".join(t.type for t in type_list)}) are known (known: {", ".join(_type_priority.keys())})'

    ordered = sorted(type_list, key=lambda t: _type_priority[t.type], reverse=True)
    return ordered[0]


@dataclass
class CPPParsedTypeInfo:
    '''
    A parsed type, with the type and whether it's a pointer.
    '''
    # The type name (`int`, `vector<float`, etc.)
    name: str

    # Pointer, and how many (2 for `int**`, 0 for `int`, etc.)
    pointer_depth: int

    def __str__(self):
        return self.name + '*' * self.pointer_depth

def parse_type(t_name: str) -> CPPParsedTypeInfo:
    '''Convert a type name string into info for a type

    Args:
        t_name (str): The type name (`float`, `float*`)

    Returns:
        CPPParsedTypeInfo: Parsed info from the type
    '''
    ptr_depth = 0
    while True:
        t_name = t_name.strip()
        if t_name.endswith('*'):
            ptr_depth += 1
            t_name = t_name[:-1]
        else:
            break

    return CPPParsedTypeInfo(t_name, ptr_depth)
