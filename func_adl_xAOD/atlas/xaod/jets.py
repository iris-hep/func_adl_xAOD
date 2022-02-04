# Code to aid with accessing jet collections
import ast

import func_adl_xAOD.common.cpp_ast as cpp_ast


def getAttribute(call_node: ast.Call):
    '''
    This is a common mistake as this is how it is written in C++. However, because we do
    not do templates, we need to do something more explicit. So, bomb out here.
    '''
    raise Exception("Do not call `getAttribute` - instead call `getAttributeFloat` or `getAttributeVectorFloat`.")


def get_jet_methods():
    get_attribute_float = cpp_ast.CPPCodeSpecification(
        name='getAttributeFloat',
        include_files=['vector'],
        arguments=['moment_name', ],
        code=['auto result = obj_j->getAttribute<float>(moment_name);'],
        result='result',
        cpp_return_type='float',
        method_object='obj_j',
        instance_object='xAOD::Jet_v1',
    )
    get_attribute_vector_float = cpp_ast.CPPCodeSpecification(
        name='getAttributeFloat',
        include_files=['vector'],
        arguments=['moment_name', ],
        code=['auto result = obj_j->getAttribute<std::vector<double>>(moment_name);'],
        result='result',
        cpp_return_type='double',
        cpp_return_is_collection=True,
        method_object='obj_j',
        instance_object='xAOD::Jet_v1',
    )
    return {
        'getAttribute': getAttribute,
        'getAttributeFloat': lambda call_node: cpp_ast.build_CPPCodeValue(get_attribute_float, call_node),
        'getAttributeVectorFloat': lambda call_node: cpp_ast.build_CPPCodeValue(get_attribute_vector_float, call_node),
    }
