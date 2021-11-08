import ast
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Union
from collections.abc import Iterable

from func_adl import EventDataset
import python_on_whales
from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.result_ttree import cpp_ttree_rep
from python_on_whales import docker


class xAODDataset(EventDataset):
    '''A dataset running locally
    '''
    def __init__(self,
                 files: Union[Path, str, List[Path]],
                 docker_image='atlas/analysisbase',
                 docker_tag='21.2.191'):
        '''Run on the given files

        Args:
            files (Path): Locally accessible files we are going to run on
            docker_image (str): The docker image name to run the executable
            docker_tag (str): The docker tag to use to run the executable
        '''
        super().__init__()

        if isinstance(files, str):
            f_list = [files]
        else:
            f_list = files if isinstance(files, Iterable) else [files]
        self.files = [Path(f) if not isinstance(f, Path) else f for f in f_list]

        if len(self.files) == 0:
            raise RuntimeError('No files were given to the xAODDataset - need at least one good file')

        self._docker_image = f'{docker_image}:{docker_tag}'
        self._source_file_name = 'query.cxx'

        for f in self.files:
            if not f.exists():
                raise FileNotFoundError(f'File {f} does not exist')

    def get_executor_obj(self) -> executor:
        '''Return the code that will actually generate the C++ we need to execute
        here.

        Returns:
            executor: Return the executor
        '''
        return atlas_xaod_executor()

    async def execute_result_async(self, a: ast.AST, title: str) -> Any:
        '''Take the `ast` and turn it into code and run it in docker, async.

        Args:
            a (ast.AST): The AST fo the query to run
            title (str): Title of the query

        Returns:
            Any: List of files
        '''
        # Build everything in the local temp file directory.
        with tempfile.TemporaryDirectory() as local_run_dir_p:

            # Setup the local directory and make sure it is writeable
            local_run_dir = Path(local_run_dir_p)
            local_run_dir.chmod(0o777)

            # Get the files that we can run
            exe = self.get_executor_obj()
            f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), local_run_dir)

            # Write out a file with the mapped in directories.
            # Until we better figure out how to deal with this, there are some restrictions
            # on file locations.
            datafile_dir: Optional[Path] = None
            with open(f'{local_run_dir}/filelist.txt', 'w') as flist_out:
                for u in self.files:

                    ds_path = u.parent
                    datafile = u.name
                    flist_out.write(f'/data/{datafile}\n')
                    if datafile_dir is None:
                        datafile_dir = ds_path
                    else:
                        if ds_path != datafile_dir:
                            raise RuntimeError(f'Data files must be from the same directory. Have seen {ds_path} and {datafile_dir} so far.')

            # Build the docker command and run it.
            volumes_to_mount = [
                (f_spec.output_path, '/scripts', 'ro'),
                (f_spec.output_path, '/results', ''),
                (datafile_dir, '/data/', 'ro'),
            ]

            output: str = ""
            try:
                output = docker.run(
                    self._docker_image, [f'/scripts/{f_spec.main_script}'],
                    volumes=volumes_to_mount,
                )
                self._dump_info(logging.DEBUG, output, local_run_dir)

            except python_on_whales.exceptions.DockerException as e:
                self._dump_info(logging.ERROR, output, local_run_dir)
                raise e

            # datafile_mount = f'-v {datafile_dir}:/data'
            # docker_cmd = f'docker run --rm -v {f_spec.output_path}:/scripts -v {f_spec.output_path}:/results {datafile_mount} {self._docker_image} /scripts/{f_spec.main_script}'
            # proc = await asyncio.create_subprocess_shell(docker_cmd,
            #                                              stdout=asyncio.subprocess.PIPE,  # type: ignore
            #                                              stderr=asyncio.subprocess.PIPE)  # type: ignore
            # p_stdout, p_stderr = await proc.communicate()

            # Now that we have run, we can pluck out the result.
            assert isinstance(f_spec.result_rep, cpp_ttree_rep), 'Unknown return type'
            return [_extract_result_TTree(f_spec.result_rep, local_run_dir)]

    def _dump_info(self, level, running_string: str, local_run_dir: Path):
        '''Dump the logging info from a docker run.

        Args:
            level ([type]): The logging level
            running_string (str): The string message from the run
        '''
        lg = logging.getLogger(__name__)

        lg.log(level, 'Docker Output: ')
        _dump_split_string(running_string, lambda l: lg.log(level, f'  {l}'))

        with (local_run_dir / self._source_file_name).open('r') as f:
            lg.log(level, 'C++ Source Code:')
            _dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))
        with (local_run_dir / 'ATestRun_eljob.py').open('r') as f:
            lg.log(level, 'JobOptions Source:')
            _dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))
        with (local_run_dir / 'package_CMakeLists.txt').open('r') as f:
            lg.log(level, 'CMake Source:')
            _dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))


def _dump_split_string(s: str, dump: Callable[[str], None]):
    for ll in s.split('\n'):
        dump(ll)


def _extract_result_TTree(rep: cpp_ttree_rep, run_dir):
    '''Copy the final file into a place that is "safe", and return that as a path.

    The reason for this is that the temp directory we are using is about to be deleted!

    Args:
        rep (cpp_base_rep): The representation of the final result
        run_dir ([type]): Directory where it ran

    Raises:
        Exception: [description]
    '''
    current_path = run_dir / rep.filename
    new_path = Path('.') / rep.filename
    shutil.copy(current_path, new_path)
    return new_path
