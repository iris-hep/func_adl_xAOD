import asyncio

import pytest

import func_adl_xAOD.common.cpp_types as ctyp


@pytest.fixture(autouse=True)
def clear_method_type_info():
    "Make sure the type info is erased every single run"
    ctyp.g_method_type_dict = {}
    ctyp.g_toplevel_ns = {}
    yield
    ctyp.g_method_type_dict = {}
    ctyp.g_toplevel_ns = {}


@pytest.fixture(autouse=True)
def get_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No running loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
