# Some math utilities
import ast
from typing import Callable, Dict
import func_adl_xAOD.common.cpp_ast as cpp_ast


DeltaRSpec = cpp_ast.CPPCodeSpecification(
    'DeltaR',
    ['TVector2.h', 'math.h'],
    ['eta1', 'phi1', 'eta2', 'phi2'],
    [
        'auto d_eta = eta1 - eta2;',
        'auto d_phi = TVector2::Phi_mpi_pi(phi1-phi2);',
        'auto result = sqrt(d_eta*d_eta + d_phi*d_phi);'
    ],
    'result',
    'double'
)


def DeltaR(eta1, phi1, eta2, phi2) -> float:
    'Calculate the DeltaR between two eta,phi specified vectors'
    raise NotImplementedError('DeltaR should never be called in python!')


def get_math_methods() -> Dict[str, Callable[[ast.Call], ast.Call]]:
    return {
        'DeltaR': lambda call_node: cpp_ast.build_CPPCodeValue(DeltaRSpec, call_node)
    }
