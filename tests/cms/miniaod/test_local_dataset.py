from tests.cms.miniaod.config import f_location
import pytest

python_on_whales = pytest.importorskip("python_on_whales")


@pytest.mark.cms_miniaod_runner
def test_integrated_run():
    '''Test a simple run with docker'''
    # TODO: Using the type stuff, make sure replacing Select below with SelectMany makes a good error message
    from func_adl_xAOD.cms.miniaod.local_dataset import CMSRun2miniAODDataset
    r = (CMSRun2miniAODDataset(f_location)
         .SelectMany('lambda e: e.Muons("globalMuons")')
         .Select('lambda m: m.pt()')
         .AsROOTTTree('junk.root', 'my_tree', ['muon_pt'])
         .value())

    assert len(r) == 1


@pytest.fixture()
def docker_mock(mocker):
    'Mock the docker object'
    m = mocker.MagicMock(spec=python_on_whales.docker)

    def parse_arg(*args, **kwargs):
        v = kwargs['volumes']
        data_s = [d for d in v if d[1] == '/results']
        assert len(data_s) == 1
        data = data_s[0][0]
        (data / 'ANALYSIS.root').touch()

        return (('stdout', b'text'), ('stderr', b'text'))

    m.run.side_effect = parse_arg
    mocker.patch('func_adl_xAOD.common.local_dataset.docker', m)
    return m


def test_run(docker_mock):
    '''Test a simple run using docker mock'''
    from func_adl_xAOD.cms.miniaod.local_dataset import CMSRun2miniAODDataset
    r = (CMSRun2miniAODDataset(f_location)
         .SelectMany('lambda e: e.Muons("globalMuons")')
         .Select('lambda m: m.pt()')
         .AsROOTTTree('junk.root', 'my_tree', ['muon_pt'])
         .value())

    assert len(r) == 1

