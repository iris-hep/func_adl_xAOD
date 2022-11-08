# Contains test that will run the full query.
import asyncio
import logging
import os

import pytest
from func_adl_xAOD.common.math_utils import DeltaR  # NOQA
from tests.atlas.r22_xaod.config import f_single, run_long_running_tests
from tests.atlas.r22_xaod.utils import as_pandas

# These are *long* tests and so should not normally be run. Each test can take of order 30 seconds or so!!
pytestmark = run_long_running_tests

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore


@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)


@pytest.fixture()
def event_loop():
    "Get the loop done right on windows"
    if os.name == "nt":
        loop = asyncio.ProactorEventLoop()  # type: ignore
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()


def test_flatten_array():
    # A very simple flattening of arrays
    training_df = as_pandas(
        f_single.SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")').Select(
            "lambda j: j.pt()/1000.0"
        )
    )
    assert abs(training_df.iloc[0]["col1"] - 21.733) < 0.001  # type: ignore ()
    assert int(training_df.iloc[0]["col1"]) != int(training_df.iloc[2]["col1"])  # type: ignore
