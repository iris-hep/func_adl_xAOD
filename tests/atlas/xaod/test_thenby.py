import pytest

from tests.atlas.xaod.utils import atlas_xaod_dataset
from tests.utils.general import get_lines_of_code


@pytest.mark.parametrize("primary", ["OrderBy", "OrderByDescending"])
@pytest.mark.parametrize("secondary", ["ThenBy", "ThenByDescending"])
def test_thenby_shared_sort(primary, secondary):
    result = (
        atlas_xaod_dataset()
        .Select(
            f"lambda e: e.Jets('AntiKt4EMTopoJets').{primary}(lambda j: j.pt() > 50000)"
            f".{secondary}(lambda j: j.eta()).ThenBy(lambda j: j.pt()).Select(lambda j: j.pt())"
        )
        .value()
    )
    code = "\n".join(get_lines_of_code(result))
    assert code.count("std::stable_sort") == 1
    assert "std::sort(" not in code
    assert "std::get<2>" in code
    primary_op = ">" if primary.endswith("Descending") else "<"
    secondary_op = ">" if secondary.endswith("Descending") else "<"
    assert f"std::get<0>(a.first) {primary_op} std::get<0>(b.first)" in code
    assert f"std::get<1>(a.first) {secondary_op} std::get<1>(b.first)" in code


def test_thenby_requires_adjacent_primary_order():
    with pytest.raises(ValueError, match="immediately follow an ordering"):
        atlas_xaod_dataset().Select(
            "lambda e: e.Jets('AntiKt4EMTopoJets').ThenBy(lambda j: j.pt()).Count()"
        ).value()
    with pytest.raises(ValueError, match="immediately follow an ordering"):
        atlas_xaod_dataset().Select(
            "lambda e: e.Jets('AntiKt4EMTopoJets').OrderBy(lambda j: j.pt())"
            ".Where(lambda j: j.pt() > 0).ThenBy(lambda j: j.eta()).Count()"
        ).value()


@pytest.mark.atlas_xaod_runner
def test_thenby_atlas_data(tmp_path):
    import awkward as ak
    import uproot
    from func_adl_xAOD.atlas.xaod import xAODDataset
    from tests.atlas.xaod.config import f_location
    from tests.utils.base import evaluate_root_ttree

    jets = "e.Jets('AntiKt4EMTopoJets')"
    expressions = [
        f"{jets}.Select(lambda j: j.pt())",
        f"{jets}.Select(lambda j: j.eta())",
    ]
    directions = [(False, False), (False, True), (True, False), (True, True)]
    for primary_desc, secondary_desc in directions:
        primary = "OrderByDescending" if primary_desc else "OrderBy"
        secondary = "ThenByDescending" if secondary_desc else "ThenBy"
        expressions.append(
            f"{jets}.{primary}(lambda j: j.pt() > 50000)"
            f".{secondary}(lambda j: j.eta()).ThenBy(lambda j: j.pt()).Select(lambda j: j.pt())"
        )
    expressions += [
        f"{jets}.OrderBy(lambda j: True).ThenBy(lambda j: True).Select(lambda j: j.pt())",
        f"{jets}.Where(lambda j: j.pt() < 0).OrderBy(lambda j: j.pt()).ThenBy(lambda j: j.eta()).Select(lambda j: j.pt())",
    ]
    query = xAODDataset(f_location, output_directory=tmp_path).Select(
        "lambda e: (" + ", ".join(expressions) + ")"
    )
    files = evaluate_root_ttree(
        query,
        "thenby.root",
        "thenby",
        ["pt", "eta", "aa", "ad", "da", "dd", "stable", "empty"],
    )
    with uproot.open(files[0]) as root_file:
        rows = ak.to_list(root_file["thenby"].arrays())
    assert len(rows) == 10
    assert any(
        len(set(pt > 50000 for pt in row["pt"])) < len(row["pt"]) for row in rows
    )
    for row in rows:
        for (primary_desc, secondary_desc), name in zip(
            directions, ["aa", "ad", "da", "dd"]
        ):
            pairs = list(zip(row["pt"], row["eta"]))
            expected = sorted(
                pairs,
                key=lambda p: (
                    -int(p[0] > 50000) if primary_desc else int(p[0] > 50000),
                    -p[1] if secondary_desc else p[1],
                    p[0],
                ),
            )
            assert row[name] == [p[0] for p in expected]
        assert row["stable"] == row["pt"]
        assert row["empty"] == []
