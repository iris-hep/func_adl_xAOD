import pytest
import func_adl_xAOD.common.cpp_types as ctyp


@pytest.fixture(autouse=True)
def clear_method_type_info():
    'Make sure the type info is erased every single run'
    ctyp.g_method_type_dict = {}
    yield
    ctyp.g_method_type_dict = {}
