import pytest

from tests.atlas.xaod.utils import atlas_xaod_dataset  # type: ignore
from tests.utils.general import get_lines_of_code, print_lines  # type: ignore
from tests.utils.locators import (  # type: ignore
    find_line_numbers_with,
    find_line_with,
    find_open_blocks,
)


def OrderByDescending(source, key_func):
    raise RuntimeError("OrderByDescending should be processed by the backend")


def test_orderby_preserves_const_atlas_elements():
    result = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").OrderBy(lambda j: j.pt()).First().pt()
        )
        .value()
    )
    assert any(
        "std::pair<double, const xAOD::Jet*>" in line
        for line in get_lines_of_code(result)
    )


def test_orderby_first_jet_pt():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").OrderBy(lambda j: j.pt()).First().pt()
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    l_collect = find_line_with(".emplace_back", lines)
    l_sort = find_line_with("std::sort", lines)
    l_sorted_loop = find_line_with("for (auto &&", lines[l_sort:]) + l_sort
    l_first = find_line_numbers_with("if (is_first", lines)

    assert l_collect < l_sort < l_sorted_loop
    assert len(l_first) == 2
    assert l_sorted_loop < l_first[0]
    assert any(".second->pt()" in line for line in lines)


def test_orderby_descending_first_jet_pt():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .OrderByDescending(lambda j: j.pt())
            .First()
            .pt()
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    l_collect = find_line_with(".emplace_back", lines)
    l_sort = find_line_with("std::sort", lines)
    l_sorted_loop = find_line_with("for (auto &&", lines[l_sort:]) + l_sort

    assert l_collect < l_sort < l_sorted_loop
    assert "a.first > b.first" in lines[l_sort]
    assert any(".second->pt()" in line for line in lines)


def test_orderby_descending_normalized_ast_call():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: OrderByDescending(e.Jets("AntiKt4EMTopoJets"), lambda j: j.pt())
            .First()
            .pt()
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    l_sort = find_line_with("std::sort", lines)
    assert "a.first > b.first" in lines[l_sort]


def test_orderby_after_where_collects_inside_filter():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Where(lambda j: j.pt() > 10.0)
            .OrderBy(lambda j: j.eta())
            .Select(lambda j: j.pt())
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    l_collect = find_line_with(".emplace_back", lines)
    l_sort = find_line_with("std::sort", lines)
    l_select = find_line_with(".second->pt()", lines)
    active_blocks = find_open_blocks(lines[:l_collect])

    assert any(">10.0" in block for block in active_blocks)
    assert l_collect < l_sort < l_select


def test_orderby_select_uses_sorted_sequence_for_output():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .OrderBy(lambda j: j.pt())
            .Select(lambda j: j.pt())
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    l_sort = find_line_with("std::sort", lines)
    l_push_output = find_line_with("push_back", lines[l_sort:]) + l_sort

    assert ".second->pt()" in lines[l_push_output]


def test_orderby_first_empty_sequence_failure_path():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Where(lambda j: j.pt() < 0.0)
            .OrderBy(lambda j: j.pt())
            .First()
            .pt()
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    assert find_line_with("First() called on an empty sequence", lines) > 0


def test_orderby_selected_sequence_first_can_be_counted():
    r = (
        atlas_xaod_dataset()
        .Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .OrderBy(lambda j: j.pt())
            .Select(lambda j: e.Tracks("InDetTrackParticles"))
            .First()
            .Count()
        )
        .value()
    )

    lines = get_lines_of_code(r)
    print_lines(lines)

    assert len(find_line_numbers_with("for (auto &&", lines)) == 3
    assert find_line_with("std::sort", lines) > 0
    assert find_line_with("+1", lines) > 0


@pytest.mark.atlas_xaod_runner
@pytest.mark.parametrize("descending", [False, True])
def test_orderby_atlas_data(tmp_path, descending):
    """Compare generated ATLAS sorting with Python on the same event data."""
    import awkward as ak
    import uproot
    from func_adl_xAOD.atlas.xaod import xAODDataset
    from tests.atlas.xaod.config import f_location
    from tests.utils.base import evaluate_root_ttree

    operation = "OrderByDescending" if descending else "OrderBy"
    query = xAODDataset(f_location, output_directory=tmp_path).Select(
        "lambda e: ("
        "e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()), "
        f"e.Jets('AntiKt4EMTopoJets').{operation}(lambda j: j.pt()).Select(lambda j: j.pt()), "
        f"e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()).{operation}(lambda p: p), "
        f"e.Jets('AntiKt4EMTopoJets').Where(lambda j: j.pt() > 30000).{operation}(lambda j: j.pt()).Select(lambda j: j.pt()), "
        f"e.Jets('AntiKt4EMTopoJets').{operation}(lambda j: j.pt()).First().pt(), "
        f"e.Jets('AntiKt4EMTopoJets').Where(lambda j: j.pt() < 0).{operation}(lambda j: j.pt()).Select(lambda j: j.pt()))"
    )
    files = evaluate_root_ttree(
        query,
        "ordering.root",
        "ordering",
        ["all", "objects", "scalars", "filtered", "first", "empty"],
    )
    with uproot.open(files[0]) as root_file:
        rows = ak.to_list(root_file["ordering"].arrays())
    assert len(rows) == 10
    for row in rows:
        expected = sorted(row["all"], reverse=descending)
        assert row["objects"] == row["scalars"] == expected
        assert row["filtered"] == sorted(
            [v for v in row["all"] if v > 30000], reverse=descending
        )
        assert row["first"] == expected[0]
        assert row["empty"] == []
