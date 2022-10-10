import asyncio
import logging
import os
import sys

import pytest
from func_adl import Range
from func_adl_xAOD.cms.miniaod import isNonnull
from tests.cms.miniaod.config import f_single, run_long_running_tests
from tests.cms.miniaod.utils import as_pandas

pytestmark = run_long_running_tests

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)

# def test_select_pt_of_global_muons():
#     training_df = as_pandas(f_single
#                             .SelectMany('lambda e: e.Muons("slimmedMuons")')
#                             .Select('lambda m: m.pt()'))

#     assert training_df.iloc[0]['col1'] == 12.901309967041016
#     assert training_df.iloc[1]['col1'] == 7.056070327758789
#     assert training_df.iloc[-1]['col1'] == 49.50603485107422


# def test_select_twice_pt_of_global_muons():
#     training_df = as_pandas(f_single
#                             .SelectMany('lambda e: e.Muons("slimmedMuons")')
#                             .Select('lambda m: m.pt() * 2'))

#     assert training_df.iloc[0]['col1'] == 25.80261993408203
#     assert training_df.iloc[1]['col1'] == 14.112140655517578
#     assert training_df.iloc[-1]['col1'] == 99.01206970214844


# def test_select_eta_of_global_muons():
#     training_df = as_pandas(f_single
#                             .SelectMany('lambda e: e.Muons("slimmedMuons")')
#                             .Select('lambda m: m.eta()'))

#     assert training_df.iloc[0]['col1'] == -1.2982407808303833
#     assert training_df.iloc[1]['col1'] == -1.1389755010604858
#     assert training_df.iloc[-1]['col1'] == 1.2762727737426758


# def test_select_pt_eta_of_global_muons():
#     training_df = as_pandas(f_single
#                             .SelectMany('lambda e: e.Muons("slimmedMuons")')
#                             .Select('lambda m: m.pt() + m.eta()'))

#     assert training_df.iloc[0]['col1'] == 11.603069186210632
#     assert training_df.iloc[1]['col1'] == 5.917094826698303
#     assert training_df.iloc[-1]['col1'] == 50.782307624816895


def test_select_hitpattern_of_global_muons():
    sys.setrecursionlimit(10000)
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.Muons("slimmedMuons")')
                            #.Select(lambda m: m.pseudoTrack())
                            #.Select(lambda m: m.hitpattern())
                            .Select(lambda hp: Range(0, hp.numberOfHits())
                                    .Select(lambda i: hp.getHitPattern(i))))

    assert training_df.iloc[0]['col1'] == 1160.0
    assert training_df.iloc[1]['col1'] == 1168.0
    assert training_df.iloc[-1]['col1'] == 248.0


# def test_isnonull_call():
#     ''' Make sure the non null call works properly. This is tricky because of the
#     way objects are used here - both as a pointer and an object, so the code
#     has to work just right.
#     '''
#     training_df = as_pandas(
#         f_single
#         .Select(lambda e: e.Muons("muons"))
#         .Select(lambda muons: muons.Where(lambda m: isNonnull(m.globalTrack())))
#         .Select(lambda muons: muons.Count())
#     )
#     assert training_df.iloc[0]['col1'] == 3


# def test_sumChargedHadronPt():
#     training_df = as_pandas(
#         f_single
#         .SelectMany(lambda e: e.Muons("muons"))
#         .Select(lambda m: (m.pfIsolationR04()).sumChargedHadronPt)
#     )
#     assert training_df.iloc[0]['col1'] == 1.6184179782867432
#     assert training_df.iloc[1]['col1'] == 0.8745666742324829
#     assert training_df.iloc[-1]['col1'] == 0.0
