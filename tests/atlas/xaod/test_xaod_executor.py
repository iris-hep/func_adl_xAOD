import ast
import re
from math import sin

import pytest
from func_adl import Range

from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor
from func_adl_xAOD.common.math_utils import DeltaR
from tests.atlas.xaod.utils import atlas_xaod_dataset, exe_from_qastle  # type: ignore
from tests.utils.general import get_lines_of_code, print_lines  # type: ignore
from tests.utils.locators import find_line_numbers_with  # type: ignore
from tests.utils.locators import find_line_with, find_open_blocks

# Tests that make sure the xaod executor is working correctly


class Atlas_xAOD_File_Type:
    def __init__(self):
        pass


def test_dict_output():
    "This is integration testing - making sure the dict to root conversion works"
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.EventInfo("EventInfo").runNumber())
        .Select(lambda e: {"run_number": e})
        .value()
    )
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test_dict_output_fail_expansion():
    my_old_dict = {1: "hi"}
    with pytest.raises(ValueError):
        atlas_xaod_dataset().Select(
            lambda e: e.EventInfo("EventInfo").runNumber()
        ).Select(lambda e: {"run_number": e, **my_old_dict}).value()


def test_per_event_item():
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.EventInfo("EventInfo").runNumber())
        .value()
    )
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test_per_jet_item():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1 == ["for" in a for a in active_blocks].count(True)


def test_per_jet_dict_items():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(
            lambda j: {
                "pt": j.pt(),
                "eta": j.eta(),
            }
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)

    l_pt = lines[find_line_with("->pt()", lines)]
    l_eta = lines[find_line_with("->eta()", lines)]

    obj_finder = re.compile(r".*(i_obj[0-9]+)->.*")
    l_pt_r = obj_finder.match(l_pt)
    l_eta_r = obj_finder.match(l_eta)

    assert l_pt_r is not None
    assert l_eta_r is not None

    assert l_pt_r[1] == l_eta_r[1]


def test_output_datatype_string():
    "Make sure a string coming back works"
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "xAOD::Jet",
                "method_name": "a_string",
                "return_type": "string",
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.a_string())
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)

    # Good enough to check that the class var that will record the ttree
    # variable is set correctly.
    vs = r.QueryVisitor._gc._class_vars
    assert len(vs) == 1
    assert vs[0]._cpp_type.type == "string"


def test_builtin_abs_function():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: abs(j.pt())))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_abs = find_line_with("std::abs", lines)
    assert "->pt()" in lines[l_abs]


def test_builtin_sin_function_no_math_import():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: sin(j.pt())))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_abs = find_line_with("std::sin", lines)
    assert "->pt()" in lines[l_abs]


def test_builtin_sin_function_math_import():
    # The following statement should be a straight sequence, not an array.
    from math import sin

    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: sin(j.pt())))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_abs = find_line_with("std::sin", lines)
    assert "->pt()" in lines[l_abs]


def test_if_expr():
    r = (
        atlas_xaod_dataset(qastle_roundtrip=True)
        .SelectMany(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: 1.0 if j.pt() > 10.0 else 2.0
            )
        )
        .value()
    )
    # Make sure that a test around 10.0 occurs.
    lines = get_lines_of_code(r)
    print_lines(lines)
    lines = [ln for ln in lines if "10.0" in ln]
    assert len(lines) == 1
    assert "if " in lines[0]


def test_constant():
    r = (
        atlas_xaod_dataset(qastle_roundtrip=True)
        .Select(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: 1.0))
        .value()
    )
    # Make sure that a test around 10.0 occurs.
    lines = get_lines_of_code(r)
    print_lines(lines)
    push_line = [index for index, line in enumerate(lines) if "push_back(1.0)" in line]
    assert len(push_line) == 1
    assert lines[push_line[0] + 1].strip() == "}"


def test_where_at_top_level():
    "Complex top level cut does not get C++ if statement in right place"
    r = (
        atlas_xaod_dataset()
        .Where(lambda e: e.EventInfo("event_info").run_number > 10)
        .Select(lambda e: e.Jets("hi").Count())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure we are grabbing the jet container and the fill at the same indent level.
    i_jet = find_line_with("const xAOD::JetContainer* jets", lines)
    i_fill = find_line_with("->Fill()", lines)
    assert len(lines[i_jet]) - len(lines[i_jet].lstrip()) == len(lines[i_fill]) - len(
        lines[i_fill].lstrip()
    )


def test_where_at_top_level_sub_count():
    "Complex top level cut does not get C++ if statement in right place"
    r = (
        atlas_xaod_dataset()
        .Where(lambda e: e.Jets("hi").Count() > 0)
        .Select(lambda e: e.Jets("hi").Count())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure we are grabbing the jet container and the fill at the same indent level.
    i_fill = find_line_with("->Fill()", lines)
    assert 4 == len(lines[i_fill]) - len(lines[i_fill].lstrip())


def test_where_at_top_level_First():
    "Complex top level cut does not get C++ if statement in right place"
    r = (
        atlas_xaod_dataset()
        .Where(lambda e: e.Jets("hi").First().pt() > 1001.0)
        .Select(lambda e: e.Jets("hi").Count())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure we are grabbing the jet container and the fill at the same indent level.
    i_pt_test = find_line_with(">1001.0", lines)
    i_fill = find_line_with("->Fill()", lines)
    assert (len(lines[i_pt_test]) - len(lines[i_pt_test].lstrip()) + 2) == len(
        lines[i_fill]
    ) - len(lines[i_fill].lstrip())


def test_where_at_top_level_First_and_count():
    "Complex top level cut does not get C++ if statement in right place"
    r = (
        atlas_xaod_dataset()
        .Where(lambda e: len(e.Jets("hi")) > 10 and e.Jets("hi").First().pt() > 1001.0)
        .Select(lambda e: e.Jets("hi").Count())
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure we are grabbing the jet container and the fill at the same indent level.
    i_pt_test = find_line_with(">1001.0", lines)
    i_fill = find_line_with("->Fill()", lines)
    assert 4 == len(lines[i_fill]) - len(lines[i_fill].lstrip())


def test_where_top_level_loop_select():
    "If we put an array selection after a top level loop, make sure if statement is right"
    r = (
        atlas_xaod_dataset()
        .Where(lambda e: 1 > 10)
        .Select(lambda e: [j.pt() for j in e.Jets("hi")])
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure we are grabbing the jet container and the fill at the same indent level.
    i_if = find_line_with("1>10", lines)
    i_if_indent = len(lines[i_if]) - len(lines[i_if].lstrip())
    i_fill = find_line_with("->Fill()", lines)
    i_fill_indent = len(lines[i_fill]) - len(lines[i_fill].lstrip())
    assert i_if_indent < i_fill_indent


def test_per_jet_item_with_where():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.pt() > 40.0)
        .Select(lambda j: {"JetPts": j.pt()})  # type: ignore
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_JetPts", lines)
    assert "Fill()" in lines[l_jet_pt + 1]


def test_and_clause_in_where():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.pt() > 40.0 and j.eta() < 2.5)
        .Select(lambda j: j.pt())
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_if = [ln for ln in lines if "if (" in ln]
    assert len(l_if) == 2
    assert l_if[0] == l_if[1]


def test_or_clause_in_where():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: j.pt() > 40.0 or j.eta() < 2.5)
        .Select(lambda j: j.pt())
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_if = [ln for ln in lines if "if (" in ln]
    assert len(l_if) == 2
    assert l_if[0] != l_if[1]
    assert l_if[0].replace("!", "") == l_if[1]


def test_nested_lambda_argument_name_with_monad():
    # Need both the monad and the "e" reused to get this error!
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: (e.Electrons("Electrons"), e.Muons("Muons")))
        .Select(lambda e: e[0].Select(lambda e: e.E()))
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push = find_line_with("push_back", lines)
    assert "->E()" in lines[l_push]


def test_dict_simple_reference():
    "Dictionary references should be resolved automatically"
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: {"e_list": e.Electrons("Electrons"), "m_list": e.Muons("Muons")}
        )
        .Select(lambda e: e.e_list.Select(lambda e: e.E()))  # type: ignore
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push = find_line_with("push_back", lines)
    assert "->E()" in lines[l_push]
    r = find_line_with("muon", lines, throw_if_not_found=False)
    assert r == -1


def test_dict_simple_reference_prop_lookup():
    "Dictionary references should be resolved automatically"
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: {"e_list": e.Electrons("Electrons"), "m_list": e.Muons("Muons")}
        )
        .Select(lambda e: e["e_list"].Select(lambda e: e.E()))
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push = find_line_with("push_back", lines)
    assert "->E()" in lines[l_push]
    r = find_line_with("muon", lines, throw_if_not_found=False)
    assert r == -1


def test_dict_code_not_used_not_generated():
    "Dictionary references should be resolved automatically"
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: {
                "e_list": e.Electrons("Electrons"),
                "m_list": e.Muons("Muons").First().pt() + 33,
            }
        )
        .Select(lambda e: e["e_list"].Select(lambda e: e.E()))
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push = find_line_with("push_back", lines)
    assert "->E()" in lines[l_push]
    r = find_line_with("muon", lines, throw_if_not_found=False)
    assert r == -1


def test_result_awkward():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.pt())
        .value()
    )
    # Make sure that the tree Fill is at the same level as the _JetPts2 getting set.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_col1", lines)
    assert "Fill()" in lines[l_jet_pt + 1]


def test_per_jet_item_with_event_level():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()),
                e.EventInfo("EventInfo").runNumber(),
            )
        )
        .SelectMany(
            lambda ji: ji[0].Select(
                lambda pt: {  # type: ignore
                    "JetPt": pt,
                    "runNumber": ji[1],
                }  # type: ignore
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_JetPt", lines)
    l_run_num = find_line_with("_runNumber", lines)
    l_fill = find_line_with("->Fill()", lines)
    assert l_jet_pt + 1 == l_run_num
    assert l_run_num + 1 == l_fill


def test_func_sin_call():
    atlas_xaod_dataset().Select(
        lambda e: sin(e.EventInfo("EventInfo").runNumber())
    ).value()


def test_per_jet_item_as_call():
    atlas_xaod_dataset().SelectMany(lambda e: e.Jets("bogus")).Select(
        lambda j: j.pt()
    ).value()


def test_Select_is_an_array_with_where():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda j: j.pt() / 1000.0)
            .Where(lambda jpt: jpt > 10.0)
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0 == ["for" in a for a in active_blocks].count(True)


def test_Select_is_an_array():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0 == ["for" in a for a in active_blocks].count(True)


def test_Select_1D_array_with_Where():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Where(lambda j1: j1.pt() > 10)
            .Select(lambda j: j.pt())
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0 == ["for" in a for a in active_blocks].count(True)

    push_back = find_line_with("push_back", lines)
    active_blocks = find_open_blocks(lines[:push_back])
    assert 1 == ["if" in a for a in active_blocks].count(True)


def test_Select_is_not_an_array():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1 == ["for" in a for a in active_blocks].count(True)


def test_Select_Multiple_arrays():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt() / 1000.0),
                e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.eta()),
            )
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 2 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0 == ["for" in a for a in active_blocks].count(True)


def test_Select_Multiple_arrays_2_step():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(
            lambda jets: (
                jets.Select(lambda j: j.pt() / 1000.0),
                jets.Select(lambda j: j.eta()),
            )
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push_back = find_line_numbers_with("push_back", lines)
    assert all(
        [
            len([ln for ln in find_open_blocks(lines[:pb]) if "for" in ln]) == 1
            for pb in l_push_back
        ]
    )
    assert 2 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0 == ["for" in a for a in active_blocks].count(True)


def test_Select_of_2D_array():
    # This should generate a 2D array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: e.Electrons("Electrons").Select(lambda e: e.pt())
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)

    l_vector_decl = find_line_with("vector<double>", lines)
    l_vector_active = len(find_open_blocks(lines[:l_vector_decl]))

    l_first_push = find_line_numbers_with("push_back", lines)
    assert len(l_first_push) == 2
    l_first_push_active = len(find_open_blocks(lines[: l_first_push[0]]))
    assert (l_vector_active + 1) == l_first_push_active

    # Now, make sure the second push_back is at the right level.
    l_second_push_active = len(find_open_blocks(lines[: l_first_push[1]]))
    assert (l_second_push_active + 1) == l_first_push_active


def test_Select_of_2D_with_where():
    # This should generate a 2D array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: e.Electrons("Electrons")
                .Where(lambda ele: ele.pt() > 10)
                .Select(lambda e: e.pt())
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)

    l_vector_decl = find_line_with("vector<double>", lines)
    l_vector_active = len(find_open_blocks(lines[:l_vector_decl]))

    l_first_push = find_line_with("push_back", lines)
    l_first_push_active = len(find_open_blocks(lines[:l_first_push]))
    assert (
        l_vector_active + 2
    ) == l_first_push_active  # +2 because it is inside the for loop and the if block


def test_Select_of_3D_array():
    # This should generate a 2D array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: e.Electrons("Electrons").Select(
                    lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt())
                )
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)

    l_vector_decl = find_line_with("vector<double> ", lines)
    l_vector_active = len(find_open_blocks(lines[:l_vector_decl]))

    l_vector_double_decl = find_line_with("vector<std::vector<double>>", lines)
    l_vector_double_active = len(find_open_blocks(lines[:l_vector_double_decl]))

    assert l_vector_active == (l_vector_double_active + 1)


def test_Select_of_2D_array_with_tuple():
    # We do not support structured output - so array or array(array), but not array(array, array),
    # at least not yet. Make sure error is reasonable.
    with pytest.raises(Exception) as e:
        atlas_xaod_dataset().Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: (j.pt() / 1000.0, j.eta())
            )
        ).value()

    assert "data structures" in str(e.value)


def test_SelectMany_of_tuple_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: (j.pt() / 1000.0, j.eta())
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0 == ["push_back" in ln for ln in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1 == ["for" in a for a in active_blocks].count(True)


def test_generate_binary_operators():
    # Make sure the binary operators work correctly - that they don't cause a crash in generation.
    ops = ["+", "-", "*", "/", "%"]
    for o in ops:
        r = (
            atlas_xaod_dataset()
            .SelectMany(
                f'lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt(){o}1)'
            )
            .value()
        )
        lines = get_lines_of_code(r)
        print_lines(lines)
        _ = find_line_with(f"pt(){o}1", lines)


def test_generate_binary_operator_pow():
    # Make sure the pow operator works correctly - that it doesn't cause a crash in generation.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt() ** 2))
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l1 = find_line_with("pow(i_obj", lines)
    l2 = find_line_with("->pt(), 2)", lines)
    assert l1 == l2


def test_generate_binary_operator_unsupported():
    # Make sure an unsupported binary operator triggers an exception
    with pytest.raises(Exception) as e:
        atlas_xaod_dataset().SelectMany(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt() // 2)
        ).value()

    assert "//" in str(e)


def test_generate_unary_operations():
    ops = ["+", "-"]
    for o in ops:
        r = (
            atlas_xaod_dataset()
            .SelectMany(
                f'lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()+({o}1))'
            )
            .value()
        )
        lines = get_lines_of_code(r)
        print_lines(lines)
        _ = find_line_with(f"pt()+({o}(1))", lines)


def test_generate_unary_not():
    r = (
        atlas_xaod_dataset()
        .SelectMany(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: not (j.pt() > 50.0))
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    _ = find_line_with("!(", lines)


def test_per_jet_with_matching():
    # Trying to repro a bug we saw in the wild
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets"),
                e.TruthParticles("TruthParticles").Where(lambda tp1: tp1.pdgId() == 35),
            )
        )
        .SelectMany(
            lambda ev: ev[0].Select(
                lambda j1: (
                    j1,
                    ev[1].Where(
                        lambda tp2: DeltaR(tp2.eta(), tp2.phi(), j1.eta(), j1.phi())
                        < 0.4
                    ),
                )
            )
        )
        .Select(
            lambda ji: {
                "JetPts": ji[0].pt(),  # type: ignore
                "NumLLPs": ji[1].Count(),  # type: ignore
            }
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_JetPts", lines)
    l_nllp = find_line_with("_NumLLPs", lines)
    l_fill = find_line_with("->Fill()", lines)
    assert l_jet_pt + 1 == l_nllp
    assert l_nllp + 1 == l_fill


def test_per_jet_with_matching_and_zeros():
    # Trying to repro a bug we saw in the wild
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets"),
                e.TruthParticles("TruthParticles").Where(lambda tp1: tp1.pdgId() == 35),
            )
        )
        .SelectMany(
            lambda ev: ev[0].Select(
                lambda j1: (
                    j1,
                    ev[1].Where(
                        lambda tp2: DeltaR(tp2.eta(), tp2.phi(), j1.eta(), j1.phi())
                        < 0.4
                    ),
                )
            )
        )
        .Select(
            lambda ji: {
                "JetPts": ji[0].pt(),  # type: ignore
                "NumLLPs": 0 if ji[1].Count() == 0 else (ji[1].First().pt() - ji[1].First().pt()),  # type: ignore
            }
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_JetPts", lines)
    l_nllp = find_line_with("_NumLLPs", lines)
    l_fill = find_line_with("->Fill()", lines)
    assert l_jet_pt + 1 == l_nllp
    assert l_nllp + 1 == l_fill


def test_per_jet_with_Count_matching():
    # Trying to repro a bug we saw in the wild
    # The problem is with the "Where" below, it gets moved way up to the top. If it is put near the top then the
    # generated code is fine. In this case, where it is currently located, the code generated to look at the DeltaR particles
    # is missed when calculating the y() component (for some reason). This bug may not be in the executor, but, rather, may
    # be in the function simplifier.
    # Also, if the "else" doesn't include a "first" thing, then things seem to work just fine too.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets"),
                e.TruthParticles("TruthParticles").Where(lambda tp1: tp1.pdgId() == 35),
            )
        )
        .SelectMany(
            lambda ev: ev[0].Select(
                lambda j1: (
                    j1,
                    ev[1].Where(
                        lambda tp2: DeltaR(tp2.eta(), tp2.phi(), j1.eta(), j1.phi())
                        < 0.4
                    ),
                )
            )
        )
        .Select(
            lambda ji: (
                ji[0].pt(),
                0 if ji[1].Count() == 0 else ji[1].First().prodVtx().y(),
            )
        )
        .Where(lambda j_all: j_all[0] > 40.0)
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    ln = find_line_numbers_with("if (0)", lines)
    assert len(ln) == 0


def test_per_jet_with_delta():
    # Trying to repro a bug we saw in the wild
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets"),
                e.TruthParticles("TruthParticles").Where(lambda tp1: tp1.pdgId() == 35),
            )
        )
        .SelectMany(
            lambda ev: ev[0].Select(
                lambda j1: (
                    j1,
                    ev[1].Where(
                        lambda tp2: DeltaR(tp2.eta(), tp2.phi(), j1.eta(), j1.phi())
                        < 0.4
                    ),
                )
            )
        )
        .Select(
            lambda ji: (
                ji[0].pt(),
                (
                    0
                    if ji[1].Count() == 0
                    else abs(ji[1].First().prodVtx().x() - ji[1].First().decayVtx().x())
                ),
            )
        )
        .Where(lambda j_all: j_all[0] > 40.0)
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_numbers = find_line_numbers_with("if (i_obj", lines)
    for line in [lines[ln] for ln in l_numbers]:
        assert "x()" not in line


def test_per_jet_with_matching_and_zeros_and_sum():
    # Trying to repro a bug we saw in the wild
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: (
                e.Jets("AntiKt4EMTopoJets"),
                e.TruthParticles("TruthParticles").Where(lambda tp1: tp1.pdgId() == 35),
            )
        )
        .SelectMany(
            lambda ev: ev[0].Select(
                lambda j1: (
                    j1,
                    ev[1].Where(
                        lambda tp2: DeltaR(tp2.eta(), tp2.phi(), j1.eta(), j1.phi())
                        < 0.4
                    ),
                )
            )
        )
        .Select(
            lambda ji: {
                "JetPts": ji[0].pt(),  # type: ignore
                "NumLLPs": 0 if ji[1].Count() == 0 else (ji[1].First().pt() - ji[1].First().pt()),  # type: ignore
                "sums": ji[0].getAttributeVectorFloat("EnergyPerSampling").Sum(),  # type: ignore
            }
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_jet_pt = find_line_with("_JetPts", lines)
    l_nllp = find_line_with("_NumLLPs", lines)
    l_fill = find_line_with("->Fill()", lines)
    assert l_jet_pt + 1 == l_nllp
    assert l_nllp + 2 == l_fill


def test_electron_and_muon_with_tuple():
    # See if we can re-create a bug we are seeing with
    # Marc's long query.
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: (e.Electrons("Electrons"), e.Muons("Muons")))
        .Select(
            lambda e: (
                e[0].Select(lambda ele: ele.E()),
                e[0].Select(lambda ele: ele.pt()),
                e[0].Select(lambda ele: ele.phi()),
                e[0].Select(lambda ele: ele.eta()),
                e[1].Select(lambda mu: mu.E()),
                e[1].Select(lambda mu: mu.pt()),
                e[1].Select(lambda mu: mu.phi()),
                e[1].Select(lambda mu: mu.eta()),
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert find_line_with("->Fill()", lines) != 0


def test_electron_and_muon_with_tuple_qastle():
    # See if we can re-create a bug we are seeing with
    # Marc's long query.
    r = (
        atlas_xaod_dataset(qastle_roundtrip=True)
        .Select(lambda e: (e.Electrons("Electrons"), e.Muons("Muons")))
        .Select(
            lambda e: (
                e[0].Select(lambda ele: ele.E()),
                e[0].Select(lambda ele: ele.pt()),
                e[0].Select(lambda ele: ele.phi()),
                e[0].Select(lambda ele: ele.eta()),
                e[1].Select(lambda mu: mu.E()),
                e[1].Select(lambda mu: mu.pt()),
                e[1].Select(lambda mu: mu.phi()),
                e[1].Select(lambda mu: mu.eta()),
            )
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert find_line_with("->Fill()", lines) != 0


def test_electron_and_muon_with_list():
    # See if we can re-create a bug we are seeing with
    # Marc's long query.
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: [e.Electrons("Electrons"), e.Muons("Muons")])
        .Select(
            lambda e: [
                e[0].Select(lambda ele: ele.E()),
                e[0].Select(lambda ele: ele.pt()),
                e[0].Select(lambda ele: ele.phi()),
                e[0].Select(lambda ele: ele.eta()),
                e[1].Select(lambda mu: mu.E()),
                e[1].Select(lambda mu: mu.pt()),
                e[1].Select(lambda mu: mu.phi()),
                e[1].Select(lambda mu: mu.eta()),
            ]
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert find_line_with("->Fill()", lines) != 0


def test_electron_and_muon_with_list_qastle():
    # See if we can re-create a bug we are seeing with
    # Marc's long query.
    r = (
        atlas_xaod_dataset(qastle_roundtrip=True)
        .Select(lambda e: [e.Electrons("Electrons"), e.Muons("Muons")])
        .Select(
            lambda e: [
                e[0].Select(lambda ele: ele.E()),
                e[0].Select(lambda ele: ele.pt()),
                e[0].Select(lambda ele: ele.phi()),
                e[0].Select(lambda ele: ele.eta()),
                e[1].Select(lambda mu: mu.E()),
                e[1].Select(lambda mu: mu.pt()),
                e[1].Select(lambda mu: mu.phi()),
                e[1].Select(lambda mu: mu.eta()),
            ]
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert find_line_with("->Fill()", lines) != 0


@pytest.mark.asyncio
async def test_electron_and_muon_from_qastle():
    q = "(call ResultTTree (call Select (call Select (call EventDataset (list 'localds:bogus')) (lambda (list e) (list (call (attr e 'Electrons') 'Electrons') (call (attr e 'Muons') 'Muons')))) (lambda (list e) (list (call (attr (subscript e 0) 'Select') (lambda (list ele) (call (attr ele 'E')))) (call (attr (subscript e 0) 'Select') (lambda (list ele) (call (attr ele 'pt')))) (call (attr (subscript e 0) 'Select') (lambda (list ele) (call (attr ele 'phi')))) (call (attr (subscript e 0) 'Select') (lambda (list ele) (call (attr ele 'eta')))) (call (attr (subscript e 1) 'Select') (lambda (list mu) (call (attr mu 'E')))) (call (attr (subscript e 1) 'Select') (lambda (list mu) (call (attr mu 'pt')))) (call (attr (subscript e 1) 'Select') (lambda (list mu) (call (attr mu 'phi')))) (call (attr (subscript e 1) 'Select') (lambda (list mu) (call (attr mu 'eta'))))))) (list 'e_E' 'e_pt' 'e_phi' 'e_eta' 'mu_E' 'mu_pt' 'mu_phi' 'mu_eta') 'forkme' 'dude.root')"
    r = await exe_from_qastle(q)
    print(r)


def test_Range_good_call():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: Range(0, 10).Select(lambda index: j.pt() * index))
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    for_loops = find_line_numbers_with("for (", lines)
    assert len(for_loops) == 2
    find_line_with("(0)", lines)
    find_line_with("(10)", lines)


def test_metadata_collection():
    "This is integration testing - making sure the dict to root conversion works"
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_atlas_event_collection_info",
                "name": "ForkInfo",
                "include_files": ["xAODEventInfo/EventInfo.h"],
                "container_type": "xAOD::EventInfo",
                "contains_collection": False,
            }
        )
        .Select(lambda e: e.ForkInfo("EventInfo").runNumber())
        .Select(lambda e: {"run_number": e})
        .value()
    )
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test_metadata_collection_bad_experiment():
    "This is integration testing - making sure the dict to root conversion works"
    with pytest.raises(ValueError) as e:
        (
            atlas_xaod_dataset()
            .MetaData(
                {
                    "metadata_type": "add_cms_aod_event_collection_info",
                    "name": "Vertex",
                    "include_files": ["DataFormats/VertexReco/interface/Vertex.h"],
                    "container_type": "reco::VertexCollection",
                    "contains_collection": True,
                    "element_type": "reco::Vertex",
                    "element_pointer": False,
                }
            )
            .Select(lambda e: e.ForkInfo("EventInfo").runNumber())
            .Select(lambda e: {"run_number": e})
            .value()
        )

    assert "backend; only" in str(e.value)


def test_metadata_job_options():
    "Integration test making sure we grab the job options"
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "Vertex",
                "script": [
                    "# hi there",
                ],
            }
        )
        .Select(lambda e: e.EventInfo("EventInfo").runNumber())
        .Select(lambda e: {"run_number": e})
        .value()
    )

    assert len(r._job_option_blocks) == 1


def test_metadata_returned_type():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "xAOD::Jet",
                "method_name": "pt",
                "return_type": "double",
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.pt() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with("->pt()*2", lines)
    assert len(value_ref) == 1


def test_metadata_returned_type_deref():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "xAOD::Jet",
                "method_name": "pt",
                "return_type": "double",
                "deref_count": 1,
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.pt() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with("->pt()*2", lines)
    assert len(value_ref) == 1
    ref_line = lines[value_ref[0]]
    assert "(*i_obj" in ref_line


def test_metadata_returned_collection():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "xAOD::Jet",
                "method_name": "pt",
                "return_type_element": "myobj",
            }
        )
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "myobj",
                "method_name": "value",
                "return_type": "double",
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .SelectMany(lambda j: j.pt())
        .Select(lambda pt: pt.value() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with(".value()*2", lines)
    assert len(value_ref) == 1


def test_metadata_returned_collection_double_ptr():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "xAOD::Jet",
                "method_name": "pt",
                "return_type_element": "myobj**",
            }
        )
        .MetaData(
            {
                "metadata_type": "add_method_type_info",
                "type_string": "myobj",
                "method_name": "value",
                "return_type": "double",
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .SelectMany(lambda j: j.pt())
        .Select(lambda pt: pt.value() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with(")->value()*2", lines)
    assert len(value_ref) == 1
    deref = find_line_numbers_with("(*", lines)
    assert len(deref) == 1


def test_executor_forgets_blocks():
    "An executor must be able to run twice, and forget between"

    from func_adl_xAOD.atlas.xaod.query_ast_visitor import atlas_xaod_query_ast_visitor
    from tests.utils.base import dataset, dummy_executor

    our_exe = atlas_xaod_executor()

    class executor_atlas_holder(dummy_executor):
        def __init__(self):
            super().__init__()

        def get_executor_obj(self) -> atlas_xaod_executor:
            return our_exe

        def get_visitor_obj(self) -> atlas_xaod_query_ast_visitor:
            return atlas_xaod_query_ast_visitor()

    class dataset_xaod(dataset):
        def __init__(self, qastle_roundtrip=False):
            super().__init__(qastle_roundtrip=qastle_roundtrip)

        def get_dummy_executor_obj(self) -> dummy_executor:
            return executor_atlas_holder()

    (
        dataset_xaod()
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "fork",
                "script": ["line1", "line2"],
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.pt())
        .value()
    )
    our_exe.reset()
    (
        dataset_xaod()
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "fork",
                "script": ["line3", "line4"],
            }
        )
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Select(lambda j: j.pt())
        .value()
    )

    our_exe.add_to_replacement_dict()


def test_add_cpp_block():
    "Make sure a block of code added and called gets inserted correctly"
    from func_adl import func_adl_callable

    def jet_clean_llp_callback(s, a: ast.Call):
        new_s = s.MetaData(
            {
                "metadata_type": "add_cpp_function",
                "name": "jet_clean_llp",
                "code": ["bool result = _Cleaning_llp->keep(*jet);\n"],
                "result": "result",
                "include_files": [],
                "arguments": ["jet"],
                "return_type": "bool",
            }
        )
        return new_s, a

    @func_adl_callable(jet_clean_llp_callback)
    def jet_clean_llp(j) -> bool: ...  # noqa

    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: jet_clean_llp(j))
        .Select(lambda j: j.pt() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with("_Cleaning_llp->keep(*i_", lines)
    assert len(value_ref) == 1


def test_add_cpp_block_arg_name_confusion():
    "Make sure code replacement is done correctly"
    from func_adl import func_adl_callable

    def jet_clean_llp_callback(s, a: ast.Call):
        new_s = s.MetaData(
            {
                "metadata_type": "add_cpp_function",
                "name": "jet_clean_llp",
                "code": ["bool result = _m_jetCleaning_llp_result->keep(*jet);\n"],
                "result": "result",
                "include_files": [],
                "arguments": ["jet"],
                "return_type": "bool",
            }
        )
        return new_s, a

    @func_adl_callable(jet_clean_llp_callback)
    def jet_clean_llp(j) -> bool: ...  # noqa

    r = (
        atlas_xaod_dataset()
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets"))
        .Where(lambda j: jet_clean_llp(j))
        .Select(lambda j: j.pt() * 2)
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    value_ref = find_line_numbers_with("_m_jetCleaning_llp_result->keep(*i_", lines)
    assert len(value_ref) == 1


def test_event_collection_too_many_arg():
    "This is integration testing - making sure the dict to root conversion works"
    with pytest.raises(ValueError) as e:
        (
            atlas_xaod_dataset()
            .Select(lambda e: e.EventInfo("EventInfo", "dork").runNumber())
            .Select(lambda e: {"run_number": e})
            .value()
        )

    assert "only one argument" in str(e)


def test_event_collection_bad_type_arg():
    "This is integration testing - making sure the dict to root conversion works"
    with pytest.raises(ValueError) as e:
        (
            atlas_xaod_dataset()
            .Select(lambda e: e.EventInfo(2).runNumber())
            .Select(lambda e: {"run_number": e})
            .value()
        )

    assert "is a string" in str(e)


def test_iterate_over_base_sequence():
    "When you try to export everything, there should be a good message"
    with pytest.raises(ValueError) as e:
        (atlas_xaod_dataset().Where(lambda e: True).value())

    assert "trying to dump all variables" in str(e)
