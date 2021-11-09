from pathlib import Path
import tempfile

from python_on_whales.exceptions import DockerException
from func_adl_xAOD.atlas.xaod import xAODDataset
from .config import f_location
import pytest


@pytest.mark.atlas_xaod_runner
def test_integrated_run():
    '''Test a simple run with docker'''
    # TODO: Using the type stuff, make sure replacing Select below with SelectMany makes a good error message
    r = (xAODDataset(f_location)
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 1


@pytest.fixture()
def docker_mock(mocker):
    'Mock the docker object'
    import python_on_whales
    m = mocker.MagicMock(spec=python_on_whales.docker)

    def parse_arg(*args, **kwargs):
        v = kwargs['volumes']
        data_s = [d for d in v if d[1] == '/results']
        assert len(data_s) == 1
        data = data_s[0][0]
        (data / 'ANALYSIS.root').touch()

        return 'this is a\ntest'

    m.run.side_effect = parse_arg
    mocker.patch('func_adl_xAOD.common.local_dataset.docker', m)
    return m


@pytest.fixture()
def docker_mock_fail(mocker):
    'Mock the docker object'
    import python_on_whales
    m = mocker.MagicMock(spec=python_on_whales.docker)

    def parse_arg(*args, **kwargs):
        from python_on_whales.exceptions import DockerException
        raise DockerException(['docker command failed'], 125)

    m.run.side_effect = parse_arg
    mocker.patch('func_adl_xAOD.common.local_dataset.docker', m)
    return m


def test_run(docker_mock):
    '''Test a simple run using docker mock'''
    # TODO: Using the type stuff, make sure replacing Select below with SelectMany makes a good error message
    r = (xAODDataset(f_location)
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 1


def test_string_file(docker_mock):
    '''Test a simple run using docker mock'''
    r = (xAODDataset(str(f_location))
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 1


def test_multiple_files(docker_mock):
    '''Test a simple run using docker mock'''
    r = (xAODDataset([f_location, f_location])
         .Select(lambda e: e.EventInfo("EventInfo").runNumber())
         .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
         .value())

    assert len(r) == 1


def test_different_directories(docker_mock):
    '''Test a simple run using docker mock'''
    with tempfile.TemporaryDirectory() as d:
        import shutil
        shutil.copy(f_location, d)
        file_two = Path(d) / f_location.name

        with pytest.raises(RuntimeError) as e:
            (xAODDataset([f_location, file_two])
                .Select(lambda e: e.EventInfo("EventInfo").runNumber())
                .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
                .value())

        assert 'same directory' in str(e)


def test_bad_file(docker_mock):
    '''Test a simple run using docker mock'''
    with pytest.raises(FileNotFoundError):
        (xAODDataset(Path('/bad/path'))
            .Select(lambda e: e.EventInfo("EventInfo").runNumber())
            .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
            .value())


def test_no_file(docker_mock):
    '''Test a simple run using docker mock'''
    with pytest.raises(RuntimeError) as e:
        (xAODDataset([])
            .Select(lambda e: e.EventInfo("EventInfo").runNumber())
            .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
            .value())

    assert 'No files' in str(e)


def test_docker_error(docker_mock_fail):
    '''Test a simple run using docker mock'''
    with pytest.raises(DockerException):
        (xAODDataset([f_location])
            .Select(lambda e: e.EventInfo("EventInfo").runNumber())
            .AsROOTTTree('junk.root', 'my_tree', ['eventNumber'])
            .value())
