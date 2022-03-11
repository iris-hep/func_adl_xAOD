# Use this node in the ast when you want to add some custom C++
#
# This is one mechanism to allow for a leaky abstraction.
import ast
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, cast

import func_adl_xAOD.common.cpp_types as ctyp
import func_adl_xAOD.common.statement as statements
from func_adl_xAOD.common.cpp_representation import (cpp_collection, cpp_value,
                                                     cpp_variable)
from func_adl_xAOD.common.cpp_vars import unique_name
from func_adl_xAOD.common.util_scope import gc_scope

# The list of methods and the re-write functions for them. Each rewrite function
# is called with the Call node, which includes arguments, names, etc. It should return
# None or a cpp_ast.
method_names = {}


class CPPCodeValue (ast.AST):
    r'''
    Represents a C++ bit of code that returns a value. Like a function call or a member call.
    Use the be-fore the wire visit phase of processing to look for a pattern that needs
    to generate AST code, like a method call. Then place this AST in place of the function.
    The back-end will then do the rendering useing the information included below.

    TODO: This should be a dataclass!
    '''

    def __init__(self):
        # Files that need to be included at the top of the generated C++ file
        self.include_files = []

        # List of link libraries
        self.link_libraries = []

        # Code that is run once at the start of each "event"
        self.initialization_code = []

        # Code that is run when the particular bit of code needs to be invoked (e.g. in the middle of a hot loop).
        # This is invoked in its own scope (between "{" and "}") so there are no variable collisions.
        self.running_code = []

        # The arguments to the function. These are "correctly" mapped into the argument values
        # that are passed to the function and then a text replacement is done in the code.
        self.args = []

        # Special replacement if this is a method call. A tuple. The first item is the string to be replaced in the
        # code. The second is the name against which we should be making the call (e.g. if j is the current jet variable,
        # the tuple might be ("obj", "j")).
        self.replacement_instance_obj = None

        # A string representing the result value. This must be a simple variable. It will get replaced
        # in all the code lines above.
        self.result: Optional[str] = None

        # Representation to use for the resulting variable. Includes C++ type information.
        # A lambda that takes teh scope as an argument and returns a cpp variable to hold things.
        self.result_rep: Optional[Callable[[gc_scope], cpp_variable]] = None

        # We have no further fields for the ast machinery to explore, so this is empty for now.
        self.fields = []


# Info used to build a code spec
@dataclass
class CPPCodeSpecification:
    # Name of the function or method
    name: str

    # List of include files that we should include accessing this guy
    include_files: List[str]

    # The names of the arguments (in python)
    arguments: List[str]

    # List of lines that will be used as the template for C++ code
    code: List[str]

    # The name of the result variable
    result: str

    # The type of the result variable, or if a collection, of the values
    cpp_return_type: str

    # True if this is a collection return type. In that case, the collection is expected
    # to obey vector like semantics
    cpp_return_is_collection: bool = False

    # The name of the object this method applies against
    method_object: Optional[str] = None

    # The name of the object if this is being used as a method (e.g. the `self` variable)
    instance_object: Optional[str] = None


def build_CPPCodeValue(spec: CPPCodeSpecification, call_node: ast.Call) -> ast.Call:
    '''
    Given the specification for a C++ code block, invoked as a function in our AST, replace
    the call node with a cpp spec callback AST so the C++ code is properly inserted into the
    call stream.


    Args:
        spec (CPPCodeSpecification): The specification, including the code, that we should insert at this call node
        call_node (ast.Call): The call node (with arguments) that we are going to replace with this
        C++ code.

    Raises:
        ValueError: Raised if something is wrong with the call site

    Returns:
        [type]: The C++ ast that can easily be emitted as code
    '''

    if len(call_node.args) != len(spec.arguments):
        raise ValueError(f"The call of {spec.name}({', '.join(spec.arguments)}) has insufficient arguments ({len(call_node.args)}).")

    if isinstance(call_node.func, ast.Attribute) and spec.method_object is None:
        raise ValueError(f"The {spec.name} is a function, but it is invoked like a method.")

    if isinstance(call_node.func, ast.Name) and spec.method_object is not None:
        raise ValueError(f"The {spec.name} is a method, but it is invoked like a function.")

    # Create an AST to hold onto all of this.
    r = CPPCodeValue()
    # We need TVector2 included here
    r.include_files += spec.include_files

    # We need all four arguments pushed through.
    r.args = spec.arguments

    # The code is three steps
    r.running_code += spec.code
    r.result = spec.result
    if spec.cpp_return_is_collection:
        r.result_rep = lambda scope: cpp_collection(unique_name(spec.name), scope=scope, collection_type=ctyp.collection(ctyp.terminal(spec.cpp_return_type)))  # type: ignore
    else:
        r.result_rep = lambda scope: cpp_variable(unique_name(spec.name), scope=scope, cpp_type=ctyp.terminal(spec.cpp_return_type))

    # If this is a mehtod, copy the info over to generate the obj reference.
    if spec.method_object is not None:
        r.replacement_instance_obj = (spec.method_object, call_node.func.value.id)  # type: ignore

    call_node.func = r  # type: ignore
    return call_node


class cpp_ast_finder(ast.NodeTransformer):
    r'''
    Look through the complete ast and replace method calls that are to a C++ plug in with a c++ ast
    node.
    '''
    def __init__(self, method_names: Dict[str, Callable[[ast.Call], ast.Call]]):
        self._method_names = method_names

    def try_call(self, name, node):
        'Try to use name to do the call. Returns (ok, result) monad'
        if name in self._method_names:
            cpp_call_ast = self._method_names[name](node)
            return (cpp_call_ast is not None, cpp_call_ast)
        return (False, None)

    def visit_Call(self, node):
        r'''
        Looking for a member call of a particular name. We rewrite that as
        another name.
        WARNING: currently the namespace is global, so the parent type doesn't matter!
        '''

        # Make sure all parts of this AST are visited properly before we attempt to
        # understand the call.
        self.generic_visit(node)

        # Examine the func to see if this is a member call.
        func = node.func
        if (type(func) is ast.Attribute) and (type(func.value) is ast.Name):
            ok, new_node = self.try_call(func.attr, node)
            if ok:
                return new_node
        elif type(func) is ast.Name:
            ok, new_node = self.try_call(func.id, node)
            if ok:
                return new_node

        return node


def process_ast_node(visitor, gc, call_node: ast.Call):
    r'''Inject the proper code into the output stream to deal with this C++ code.

    We expect this to be run on the back-end of the system.

    visitor - The node visitor that is converting the code into C++
    gc - the generated code object that we fill with actual code
    call_node - a Call ast node, with func being a CPPCodeValue.

    Result:
    representation - A value that represents the output
    '''

    # We write everything into a new scope to prevent conflicts. So we have to declare the result ahead of time.
    cpp_ast_node = cast(CPPCodeValue, call_node.func)
    result_rep = cpp_ast_node.result_rep(gc.current_scope())  # type: ignore

    gc.declare_variable(result_rep)

    # Include files and link libraries
    for i in cpp_ast_node.include_files:
        gc.add_include(i)
    for i in cpp_ast_node.link_libraries:
        gc.add_link_library(i)

    # Build the dictionary for replacement for the object we are calling
    # against, if any.
    repl_list = []
    if cpp_ast_node.replacement_instance_obj is not None:
        repl_list += [(cpp_ast_node.replacement_instance_obj[0], visitor.resolve_id(cpp_ast_node.replacement_instance_obj[1]).rep.as_cpp())]

    # Process the arguments that are getting passed to the function
    for arg, dest in zip(cpp_ast_node.args, call_node.args):
        rep = visitor.get_rep(dest)
        repl_list += [(arg, rep.as_cpp())]

    # Emit the statements.
    blk = statements.block()
    visitor._gc.add_statement(blk)

    for s in cpp_ast_node.running_code:
        l_s = s
        for src, dest in repl_list:
            l_s = l_s.replace(src, str(dest))
        blk.add_statement(statements.arbitrary_statement(l_s))

    # Set the result and close the scope
    assert cpp_ast_node.result is not None
    blk.add_statement(statements.set_var(result_rep, cpp_value(cpp_ast_node.result, gc.current_scope(), result_rep.cpp_type())))
    gc.pop_scope()

    return result_rep
