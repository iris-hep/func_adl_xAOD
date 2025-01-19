# Contains test that will run the full query.
import asyncio
import logging
import os

import pytest
from func_adl_xAOD.common.math_utils import DeltaR  # NOQA
from testfixtures import LogCapture  # type: ignore
from tests.atlas.xaod.config import f_single, run_long_running_tests
from tests.atlas.xaod.utils import as_awkward, as_pandas, as_pandas_async

# These are *long* tests and so should not normally be run. Each test can take of order 30 seconds or so!!
pytestmark = run_long_running_tests

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore


@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)


def test_select_first_of_array():
    # The hard part is that First() here does not return a single item, but, rather, an array that
    # has to be aggregated over.
    training_df = as_pandas(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda _: e.Tracks("InDetTrackParticles"))
            .First()
            .Count()
        )
    )
    assert training_df.iloc[0]["col1"] == 394
    assert training_df.iloc[1]["col1"] == 387
    assert training_df.iloc[-1]["col1"] == 381


@pytest.fixture()
def event_loop():
    "Get the loop done right on windows"
    if os.name == "nt":
        loop = asyncio.ProactorEventLoop()  # type: ignore
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_two_simultaneous_runs():
    # Test the future return stuff
    f_training_df_1 = as_pandas_async(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda j: e.Tracks("InDetTrackParticles"))
            .First()
            .Count()
        )
    )
    f_training_df_2 = as_pandas_async(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda j: e.Tracks("InDetTrackParticles"))
            .First()
            .Count()
        )
    )
    r1, r2 = await asyncio.gather(f_training_df_1, f_training_df_2)
    assert r1.iloc[0]["col1"] == 394
    assert r2.iloc[0]["col1"] == 394


def test_flatten_array():
    # A very simple flattening of arrays
    training_df = as_pandas(
        f_single.SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")).Select(
            lambda j: j.pt() / 1000.0
        )
    )
    assert abs(training_df.iloc[0]["col1"] - 52.02462890625) < 0.001  # type: ignore ()
    assert int(training_df.iloc[0]["col1"]) != int(training_df.iloc[1]["col1"])  # type: ignore


def test_simple_dict_output():
    # A very simple flattening of arrays, and the binary division operator
    training_df = as_pandas(
        f_single.SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")).Select(
            lambda j: {"JetPt": j.pt() / 1000.0}
        )
    )
    print(training_df)
    assert abs(training_df.iloc[0]["JetPt"] - 52.02462890625) < 0.001  # type: ignore ()
    assert int(training_df.iloc[0]["JetPt"]) != int(training_df.iloc[1]["JetPt"])  # type: ignore


def test_md_job_options():
    """Run object corrections as we go
    Based on the following code:
    """
    training_df = as_pandas(
        f_single.MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "sys_error_tool",
                "script": [
                    "# Set up the systematics loader/handler service:",
                    "from AnaAlgorithm.DualUseConfig import createService",
                    "from AnaAlgorithm.AlgSequence import AlgSequence",
                    "calibrationAlgSeq = AlgSequence()",
                    "sysService = createService( 'CP::SystematicsSvc', 'SystematicsSvc', sequence = calibrationAlgSeq )",
                    "sysService.sigmaRecommended = 1",
                    "# Add sequence to job",
                ],
            }
        )
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "pileup_tool",
                "script": [
                    "from AsgAnalysisAlgorithms.PileupAnalysisSequence import makePileupAnalysisSequence",
                    "pileupSequence = makePileupAnalysisSequence( 'mc' )",
                    "pileupSequence.configure( inputName = 'EventInfo', outputName = 'EventInfo_%SYS%' )",
                    "# print( pileupSequence ) # For debugging",
                    "calibrationAlgSeq += pileupSequence",
                ],
                "depends_on": ["sys_error_tool"],
            }
        )
        .MetaData(
            {
                "metadata_type": "add_job_script",
                "name": "jet_corrections",
                "script": [
                    "jetContainer = 'AntiKt4EMTopoJets'",
                    "from JetAnalysisAlgorithms.JetAnalysisSequence import makeJetAnalysisSequence",
                    "jetSequence = makeJetAnalysisSequence( 'mc', jetContainer, enableCutflow=True, enableKinematicHistograms=True )",
                    "jetSequence.configure( inputName = jetContainer, outputName = 'AnalysisJetsBase_%SYS%' )",
                    "calibrationAlgSeq += jetSequence",
                    "# print( jetSequence ) # For debugging",
                    "",
                    "# Include, and then set up the jet analysis algorithm sequence:",
                    "from JetAnalysisAlgorithms.JetJvtAnalysisSequence import makeJetJvtAnalysisSequence",
                    "jvtSequence = makeJetJvtAnalysisSequence( 'mc', jetContainer, enableCutflow=True )",
                    "jvtSequence.configure( inputName = { 'jets'      : 'AnalysisJetsBase_%SYS%' },",
                    "                       outputName = { 'jets'      : 'AnalysisJets_%SYS%' })",
                    "calibrationAlgSeq += jvtSequence",
                    "# print( jvtSequence ) # For debugging",
                    "calibrationAlgSeq.addSelfToJob( job )",  # TODO: Can I do this earlier?
                    "print(job) # for debugging",
                ],
                "depends_on": ["pileup_tool"],
            }
        )
        # TODO: get the sequence above running (add to the job)
        # TODO: Make sure we correct the proper container, and see if the jet energy changes as expected.
        .SelectMany(lambda e: e.Jets("AnalysisJets_NOSYS"))
        .Select(lambda j: {"JetPt": j.pt() / 1000.0})
    )
    print(training_df)
    assert abs(training_df.iloc[0]["JetPt"] - 50.10308984375) < 0.001  # type: ignore ()
    assert int(training_df.iloc[0]["JetPt"]) != int(training_df.iloc[1]["JetPt"])  # type: ignore


def test_event_info_includes():
    "Make sure event info is pulling in the correct include files"
    training_df = as_pandas(
        # fmt: off
        f_single
        .Select(lambda e: e.EventInfo("EventInfo"))
        .Select(lambda e: e.runNumber())
        # fmt: on
    )
    print(training_df)
    assert len(training_df) == 10


def test_single_column_output():
    # And a power operator
    training_df = as_pandas(
        f_single.SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")).Select(
            lambda j: j.pt() ** 2
        )
    )
    print(training_df)
    assert int(training_df.iloc[0]["col1"]) == 2706562012  # type: ignore
    assert int(training_df.iloc[0]["col1"]) != int(training_df.iloc[1]["col1"])  # type: ignore


def test_First_two_outer_loops():
    # THis is a little tricky because the First there is actually running over one jet in the event. Further, the Where
    # on the number of tracks puts us another level down. So it is easy to produce code that compiles, but the First's if statement
    # is very much in the wrong place.
    training_df = as_pandas(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(
                lambda j: e.Tracks("InDetTrackParticles").Where(
                    lambda t: t.pt() > 1000.0
                )
            )
            .First()
            .Count()
        )
    )
    assert training_df.iloc[0]["col1"] == 136


def test_not_in_where():
    # THis is a little tricky because the First there is actually running over one jet in the event. Further, the Where
    # on the number of tracks puts us another level down. So it is easy to produce code that compiles, but the First's if statement
    # is very much in the wrong place.
    training_df = as_pandas(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(
                lambda j: e.Tracks("InDetTrackParticles").Where(
                    lambda t: not (t.pt() > 1000.0)
                )
            )
            .First()
            .Count()
        )
    )
    assert training_df.iloc[0]["col1"] == 258


def test_first_object_in_event():
    # Make sure First puts it if statement in the right place.
    training_df = as_pandas(
        f_single.Select(lambda e: e.Jets("AntiKt4EMTopoJets").First().pt() / 1000.0)
    )
    assert int(training_df.iloc[0]["col1"]) == 52  # type: ignore


def test_no_first_object_in_event(caplog):
    "Make sure a failed first properly blows its stack"
    try:
        as_pandas(
            f_single.Select(
                lambda e: e.Jets("AntiKt4EMTopoJets")
                .Where(lambda j: j.pt() > 1000000000.0)
                .First()
                .pt()
                / 1000.0
            )
        )
    except Exception as e:
        assert "docker" in str(e)

    assert "caught exception: First() called on an empty sequence" in caplog.text


def test_no_reported_statistics():
    "Look at the log file and report if it contains a statistics line"

    with LogCapture() as l_cap:
        as_pandas(
            f_single.Select(lambda e: e.Jets("AntiKt4EMTopoJets").First().pt() / 1000.0)
        )
        assert str(l_cap).find("TFileAccessTracer   INFO    Sending") == -1


def test_first_object_in_event_with_where():
    # Make sure First puts it's if statement in the right place.
    training_df = as_pandas(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets")
            .Select(lambda j: j.pt() / 1000.0)
            .Where(lambda jpt: jpt > 10.0)
            .First()
        )
    )
    assert int(training_df.iloc[0]["col1"]) == 52  # type: ignore
    assert len(training_df) == 10


def test_truth_particles():
    training_df = as_pandas(
        f_single.Select(lambda e: e.TruthParticles("TruthParticles").Count())
    )
    assert training_df.iloc[0]["col1"] == 1450


def test_truth_particles_awk():
    training_df = as_awkward(
        f_single.Select(lambda e: e.TruthParticles("TruthParticles").Count())
    )
    print(training_df)
    assert len(training_df["col1"]) == 10


def test_1D_array():
    # A very simple flattening of arrays
    training_df = as_awkward(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt() / 1000.0)
        )
    )
    print(training_df)
    assert len(training_df["col1"]) == 10
    assert len(training_df["col1"][0]) == 9  # type: ignore


def test_2D_array():
    # A very simple flattening of arrays
    training_df = as_awkward(
        f_single.Select(
            lambda e: e.Jets("AntiKt4EMTopoJets").Select(
                lambda j: j.Jets("AntiKt4EMTopoJets").Select(
                    lambda j1: j1.pt() / 1000.0
                )
            )
        )
    )
    print(training_df)
    assert len(training_df["col1"]) == 10
    assert len(training_df["col1"][0]) == 9  # type: ignore
    assert len(training_df["col1"][0][0]) == 9  # type: ignore


def test_2D_nested_where():
    # Seen in the wild as generating bad C++.
    training_df = as_awkward(
        f_single.Select(lambda e0304: (e0304.Jets("AntiKt4EMTopoJets"), e0304))
        .Select(
            lambda e0305: (
                e0305[0].Where(
                    lambda e0352: (((e0352.pt() / 1000.0) > 20))
                    and (((abs(e0352.eta())) < 1.5))
                ),
                e0305[1],
            )
        )
        .Select(
            lambda e0317: e0317[0].Select(
                lambda e0353: e0317[1]
                .TruthParticles("TruthParticles")
                .Where(lambda e0345: (e0345.pdgId() == 11))
                .Where(
                    lambda e0346: (((e0346.pt() / 1000.0) > 20))
                    and (((abs(e0346.eta())) < 1.5))
                )
                .Where(
                    lambda e0347: (
                        DeltaR(e0353.eta(), e0353.phi(), e0347.eta(), e0347.phi()) < 0.5
                    )
                )
            )
        )
        .Select(lambda e0348: e0348.Select(lambda e0354: e0354.Count()))
    )

    print(training_df)
    a = training_df["col1"]
    assert len(a) == 10
    assert len(a[0]) == 1  # type: ignore
