# Code to do the testing starts here.
import func_adl_xAOD.common.cpp_types as ctyp
from tests.utils.locators import find_line_numbers_with, find_line_with, find_next_closing_bracket, find_open_blocks  # type: ignore
from tests.utils.general import get_lines_of_code, print_lines  # type: ignore
from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore
import re


def test_first_jet_in_event():
    atlas_xaod_dataset().Select(
        lambda e: e.Jets("bogus").Select(lambda j: j.pt()).First()
    ).value()


def test_first_after_SelectMany():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("jets")
            .SelectMany(lambda j: e.Tracks("InnerTracks"))
            .First()
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)


def test_first_after_where():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    atlas_xaod_dataset().Select(
        lambda e: e.Jets("AntiKt4EMTopoJets").Where(lambda j: j.pt() > 10).First().pt()
    ).value()


def test_first_object_in_each_event():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    atlas_xaod_dataset().Select(
        lambda e: e.Jets("AntiKt4EMTopoJets").First().pt() / 1000.0
    ).value()


def test_First_Of_Select_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: {
                "FirstJetPt": e.Jets("AntiKt4EMTopoJets")
                .Select(lambda j: j.pt() / 1000.0)
                .Where(lambda jpt: jpt > 10.0)
                .First()
            }
        )
        .value()
    )
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert all("push_back" not in ln for ln in lines)
    l_fill = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_fill])
    assert 3 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_set = find_line_with("_FirstJetPt", lines)
    active_blocks = find_open_blocks(lines[:l_set])
    assert 3 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_true = find_line_with("(true)", lines)
    active_blocks = find_open_blocks(lines[:l_true])
    assert 0 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)


def test_First_Of_Select_After_Where_is_in_right_place():
    # Make sure that we have the "First" predicate after if Where's if statement.
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda j: j.pt() / 1000.0)
            .Where(lambda jpt: jpt > 10.0)
            .First()
        )
        .value()
    )
    lines = get_lines_of_code(r)
    print_lines(lines)
    ln = find_line_with(">10.0", lines)
    # Look for the "false" that First uses to remember it has gone by one.
    assert find_line_with("false", lines[ln:], throw_if_not_found=False) > 0


def test_First_with_dict():
    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.Jets("Anti").First())
        .Select(lambda j: {"pt": j.pt(), "eta": j.eta()})
        .value()
    )
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


def test_First_with_inner_loop():
    "Check we can loop over tracks"
    ctyp.add_method_type_info(
        "xAOD::Jet",
        "Tracks",
        ctyp.terminal("std::vector<xAODTruth::TruthVertex>", p_depth=1),
    )

    r = (
        atlas_xaod_dataset()
        .Select(lambda e: e.Jets("Anti").First())
        .Select(lambda j: j.Tracks("fork"))
        .Select(
            lambda tracks: {
                "pt": tracks.Select(lambda t: t.pt()),
                "eta": tracks.Select(lambda t: t.eta()),
            }
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure the eta capture is inside the is first.
    first_lines = find_line_numbers_with("if (is_first", lines)
    assert len(first_lines) == 1
    assert lines[first_lines[0] + 1].strip() == "{"
    lines_post_if = lines[first_lines[0] + 2 :]  # noqa
    is_first_closing = find_next_closing_bracket(lines_post_if)

    eta_line = find_line_numbers_with("->eta()", lines_post_if)
    assert len(eta_line) == 1
    assert is_first_closing > eta_line[0]

    # Make sure the lookup for the tracks occurs after the is_first test.
    track_lines = find_line_numbers_with("TrackParticleContainer* result", lines)
    assert len(track_lines) == 1
    assert track_lines[0] > first_lines[0]
