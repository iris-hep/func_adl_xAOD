from typing import Iterable

import ast

import pytest

from tests.atlas.xaod.utils import atlas_xaod_dataset
from tests.utils.general import get_lines_of_code
from func_adl_xAOD.atlas.xaod.query_ast_visitor import atlas_xaod_query_ast_visitor


class Jet:
    def pt(self) -> float: ...  # noqa


class Event:
    def Jets(self, bank: str) -> Iterable[Jet]: ...  # noqa


@pytest.mark.parametrize("operation", ["Skip(1)", "Take(2)", "Skip(-1)", "Take(0)"])
def test_slice_after_filter(operation):
    result = (
        atlas_xaod_dataset()
        .Select(
            "lambda e: e.Jets('AntiKt4EMTopoJets').Where(lambda j: j.pt() > 10)"
            f".{operation}.Select(lambda j: j.pt())"
        )
        .value()
    )
    lines = get_lines_of_code(result)
    assert any("slice_index" in line and "++" in line for line in lines)


def test_last_object_and_scalar():
    for expression in ["Last().pt()", "Select(lambda j: j.pt()).Last()"]:
        result = (
            atlas_xaod_dataset()
            .Select(f"lambda e: e.Jets('AntiKt4EMTopoJets').{expression}")
            .value()
        )
        assert any(
            "Last() called on an empty sequence" in line
            for line in get_lines_of_code(result)
        )


@pytest.mark.parametrize("operation", ["Skip", "Take"])
@pytest.mark.parametrize("count", ["1.5", "True", "n", "e.EventNumber()"])
def test_invalid_slice_count(operation, count):
    with pytest.raises(ValueError, match="literal integer count"):
        atlas_xaod_dataset().Select(
            f"lambda e: e.Jets('AntiKt4EMTopoJets').{operation}({count}).Count()"
        ).value()


@pytest.mark.parametrize("operation", ["Last()", "Skip(1)", "Take(1)"])
@pytest.mark.parametrize("computed", [False, True])
@pytest.mark.parametrize("typed", [False, True])
def test_nested_sequence_items_rejected(operation, computed, typed):
    jets = "e.Jets('AntiKt4EMTopoJets')"
    inner = jets + (".Where(lambda k: k.pt() > j.pt())" if computed else "")
    source = atlas_xaod_dataset()
    if typed:
        source = source.clone_with_new_ast(source.query_ast, Event)
    query = source.Select(f"lambda e: {jets}.Select(lambda j: {inner}).{operation}")
    with pytest.raises(
        ValueError, match="sequence-valued items is unsupported"
    ) as error:
        query.value()
    assert operation.split("(")[0] in str(error.value)


@pytest.mark.parametrize("operation", ["Last", "Skip", "Take"])
def test_normalized_call_rejects_keywords(operation):
    args = "source" if operation == "Last" else "source, 2"
    node = ast.parse(f"{operation}({args}, n=3)").body[0].value
    visitor = atlas_xaod_query_ast_visitor()
    with pytest.raises(ValueError) as error:
        getattr(visitor, f"call_{operation}")(node, node.args)
    assert ast.unparse(node) in str(error.value)


@pytest.mark.atlas_xaod_runner
@pytest.mark.parametrize("typed", [False, True])
def test_sequence_operations_atlas_data(tmp_path, typed):
    import awkward as ak
    import uproot
    from func_adl_xAOD.atlas.xaod import xAODDataset
    from tests.atlas.xaod.config import f_location
    from tests.utils.base import evaluate_root_ttree

    source = xAODDataset(f_location, output_directory=tmp_path)
    if typed:
        source = source.clone_with_new_ast(source.query_ast, Event)
    skip, take = 1, 2
    query = source.Select(
        lambda e: (
            e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Last().pt(),
            e.Jets("AntiKt4EMTopoJets").Skip(n=skip).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Take(n=take).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets")
            .Where(lambda j: j.pt() > 10000)
            .Skip(1)
            .Take(2)
            .Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Take(0).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Skip(-1).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Take(-1).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()).Last(),
            e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()).Skip(skip).Take(take),
            e.Jets("AntiKt4EMTopoJets").Skip(0).Select(lambda j: j.pt()),
            e.Jets("AntiKt4EMTopoJets").First().pt(),
        )
    )
    files = evaluate_root_ttree(
        query,
        "sequence.root",
        "sequences",
        [
            "all",
            "last",
            "skip",
            "take",
            "slice",
            "zero",
            "negative_skip",
            "negative_take",
            "scalar_last",
            "scalar_slice",
            "zero_skip",
            "first",
        ],
    )
    with uproot.open(files[0]) as root_file:
        rows = ak.to_list(root_file["sequences"].arrays())
    assert len(rows) == 10
    for row in rows:
        values = row["all"]
        assert row["last"] == values[-1]
        assert row["skip"] == values[1:]
        assert row["take"] == values[:2]
        assert row["slice"] == [v for v in values if v > 10000][1:3]
        assert row["zero"] == row["negative_take"] == []
        assert row["negative_skip"] == values
        assert row["scalar_last"] == values[-1]
        assert row["scalar_slice"] == values[1:3]
        assert row["zero_skip"] == values
        assert row["first"] == values[0]


@pytest.mark.atlas_xaod_runner
def test_empty_last_atlas_data(tmp_path, caplog):
    from func_adl_xAOD.atlas.xaod import xAODDataset
    from python_on_whales.exceptions import DockerException
    from tests.atlas.xaod.config import f_location
    from tests.utils.base import evaluate_root_ttree

    source = xAODDataset(f_location, output_directory=tmp_path)
    source = source.clone_with_new_ast(source.query_ast, Event)
    query = source.Select(
        lambda e: e.Jets("AntiKt4EMTopoJets").Where(lambda j: j.pt() < 0).Last().pt()
    )
    with pytest.raises(DockerException):
        evaluate_root_ttree(query, "empty.root", "empty", ["pt"])
    assert "Last() called on an empty sequence" in caplog.text
