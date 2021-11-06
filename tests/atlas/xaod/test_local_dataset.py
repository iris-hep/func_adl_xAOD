from func_adl_xAOD.atlas.xaod import xAODDataset
from .config import f_location


def test_integrated_run():
    '''Test a simple run with docker'''
    # TODO: Using the type stuff, make sure replacing Select below with SelectMany makes a good error message
    r = (xAODDataset(f_location)
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 10


def test_run():
    '''Test a simple run using docker mock'''
    # TODO: Using the type stuff, make sure replacing Select below with SelectMany makes a good error message
    r = (xAODDataset(f_location)
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 10
