# Test the statement objects
from func_adl_xAOD.common.statement import BlockException, block, push_back, set_var
import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp

# Looking up representations in blocks


def test_create_top_level_block():
    _ = block()


def test_lookup_rep_not_in_block():
    b = block()
    assert None is b.get_rep("dude")


def test_lookup_rep_in_block():
    b = block()
    n = "dude"
    b.set_rep(n, 5)
    assert 5 == b.get_rep(n)


def test_set_rep_twice_fail():
    b = block()
    n = "dude"
    b.set_rep(n, 5)
    try:
        b.set_rep(n, 10)
        assert False
    except BlockException:
        pass


def test_set_rep_type_no_change(mocker):
    r_target = crep.cpp_value("r_target", scope=None, cpp_type=ctyp.terminal("int"))
    r_value = crep.cpp_value("r_value", scope=None, cpp_type=ctyp.terminal("int"))
    sv = set_var(r_target, r_value)

    # Create a new mock for a class that has add_line method so we can check how
    # it was called.
    e = mocker.Mock()
    sv.emit(e)

    e.add_line.assert_called_once_with("r_target = r_value;")


def test_set_rep_type_null_target(mocker):
    r_target = crep.cpp_value("r_target", scope=None, cpp_type=None)
    r_value = crep.cpp_value("r_value", scope=None, cpp_type=ctyp.terminal("int"))
    sv = set_var(r_target, r_value)

    # Create a new mock for a class that has add_line method so we can check how
    # it was called.
    e = mocker.Mock()
    sv.emit(e)

    e.add_line.assert_called_once_with("r_target = r_value;")


def test_set_rep_type_null_value(mocker):
    r_target = crep.cpp_value("r_target", scope=None, cpp_type=ctyp.terminal("int"))
    r_value = crep.cpp_value("r_value", scope=None, cpp_type=None)
    sv = set_var(r_target, r_value)

    # Create a new mock for a class that has add_line method so we can check how
    # it was called.
    e = mocker.Mock()
    sv.emit(e)

    e.add_line.assert_called_once_with("r_target = r_value;")


def test_set_rep_type_change(mocker):
    r_target = crep.cpp_value("r_target", scope=None, cpp_type=ctyp.terminal("int"))
    r_value = crep.cpp_value(
        "r_value", scope=None, cpp_type=ctyp.terminal("xAOD::Jet::Color")
    )
    sv = set_var(r_target, r_value)

    # Create a new mock for a class that has add_line method so we can check how
    # it was called.
    e = mocker.Mock()
    sv.emit(e)

    e.add_line.assert_called_once_with("r_target = static_cast<int>(r_value);")


def test_push_back_same_types(mocker):
    r_sequence = crep.cpp_value(
        "r_sequence", scope=None, cpp_type=ctyp.collection(ctyp.terminal("int"))
    )
    r_value = crep.cpp_value("r_value", scope=None, cpp_type=ctyp.terminal("int"))

    pb = push_back(r_sequence, r_value)

    e = mocker.Mock()
    pb.emit(e)

    e.add_line.assert_called_once_with("r_sequence.push_back(r_value);")


def test_push_back_null_value(mocker):
    r_sequence = crep.cpp_value(
        "r_sequence", scope=None, cpp_type=ctyp.collection(ctyp.terminal("int"))
    )
    r_value = crep.cpp_value("r_value", scope=None, cpp_type=None)

    pb = push_back(r_sequence, r_value)

    e = mocker.Mock()
    pb.emit(e)

    e.add_line.assert_called_once_with("r_sequence.push_back(r_value);")


def test_push_back_diff_types(mocker):
    r_sequence = crep.cpp_value(
        "r_sequence", scope=None, cpp_type=ctyp.collection(ctyp.terminal("int"))
    )
    r_value = crep.cpp_value(
        "r_value", scope=None, cpp_type=ctyp.terminal("xAOD::Jet::Color")
    )

    pb = push_back(r_sequence, r_value)

    e = mocker.Mock()
    pb.emit(e)

    e.add_line.assert_called_once_with(
        "r_sequence.push_back(static_cast<int>(r_value));"
    )
