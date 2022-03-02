import ast
from dataclasses import dataclass
import logging
import shutil
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

import python_on_whales
from func_adl import EventDataset
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.result_ttree import cpp_ttree_rep
from python_on_whales import docker


@dataclass
class docker_volume_info:
    # Name of the volume in docker. Will be re-used.
    docker_name: str

    # The directory where the volume should be mounted
    mount_point: str


def _docker_volume_name(info: docker_volume_info) -> str:
    return 'func_adl_' + info.docker_name


class LocalDataset(EventDataset, ABC):
    '''A dataset running locally
    '''
    def __init__(self,
                 files: Union[Path, str, List[Path], List[str]],
                 docker_image: str,
                 docker_tag: str,
                 output_directory: Optional[Path] = None):
        '''Run on the given files locally using a docker image to process them.

        When using `.value()` a list of `Path` objects is returned. All input files
        are combined into a single file. And the file is always called `ANALYSIS.root`

        NOTE:

        * The caller is responsible for the clean up of any output files that are
        generated. Use `output_directory` to control where they are written.
        * If you run multiple instances of these note that the output file is always
        called the same thing - so collisions are very likely!

        Args:
            files (Path): Locally accessible files we are going to run on
            docker_image (str): The docker image name to run the executable
            docker_tag (str): The docker tag to use to run the executable
            output_directory (Optional[Path], optional): The directory to write the output to.
                If `None` then will be written to the temp directory. Any directory passed in must
                already exist. Defaults to `None`.
        '''
        super().__init__()

        if isinstance(files, str):
            f_list = [files]
        else:
            f_list = files if isinstance(files, Iterable) else [files]
        self.files = [Path(f) if not isinstance(f, Path) else f for f in f_list]

        if len(self.files) == 0:
            raise RuntimeError('No files were given to the local dataset - need at least one good file')

        self._docker_image = f'{docker_image}:{docker_tag}'

        for f in self.files:
            if not f.exists():
                raise FileNotFoundError(f'File {f} does not exist')

        self._output_directory = output_directory if output_directory is not None \
            else Path(tempfile.tempdir)  # type: ignore

        # Put everything into the ast so that we can safely be carried over qastle and used in
        # determining a hash key to see when things change.
        self.query_ast.args.append(ast.Str(s=f'{self._docker_image}'))  # type: ignore
        self.query_ast.args.append(ast.List(elts=[ast.Str(s=str(f)) for f in self.files]))  # type: ignore

    @abstractmethod
    def get_executor_obj(self) -> executor:
        '''Return the code that will actually generate the C++ we need to execute
        here.

        Returns:
            executor: Return the executor
        '''

    @abstractmethod
    def docker_cache_volume(self) -> List[docker_volume_info]:
        '''Return info for a cache volume that can be mounted to the docker container.

        Used to cache downloaded files between runs (like calibration files).

        Returns:
            str: The volume string
        '''

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

            # Add any docker volumes in
            for v_info in self.docker_cache_volume():
                # Make sure the volume has been created
                v_name = _docker_volume_name(v_info)
                # if not docker.volume.exists(v_name):
                #     docker.volume.create(v_name)
                volumes_to_mount.append((v_name, v_info.mount_point))

            output: str = ""
            try:
                output_generator = docker.run(
                    self._docker_image, [f'/scripts/{f_spec.main_script}'],
                    volumes=volumes_to_mount,
                    remove=True,
                    stream=True,
                )
                for stream_type, stream_content in output_generator:
                    if stream_type == 'stdout':
                        output += f'{stream_content.decode()}'
                    else:
                        output += f'(stderr) {stream_content.decode()}'
                self._dump_info(logging.DEBUG, output, local_run_dir, f_spec.main_script, self._docker_image)

            except python_on_whales.exceptions.DockerException as e:
                self._dump_info(logging.ERROR, output, local_run_dir, f_spec.main_script, self._docker_image)
                raise e

            # Now that we have run, we can pluck out the result.
            assert isinstance(f_spec.result_rep, cpp_ttree_rep), 'Unknown return type'
            return [_extract_result_TTree(f_spec.result_rep, local_run_dir, self._output_directory)]

    def _dump_info(self, level, running_string: str, local_run_dir: Path, source_file_name: str, docker_image: str):
        '''Dump the logging info from a docker run.

        Args:
            level ([type]): The logging level
            running_string (str): The string message from the run
        '''
        lg = logging.getLogger(__name__)

        lg.log(level, f'Docker image and tag: {docker_image}')
        lg.log(level, 'Docker Output: ')
        _dump_split_string(running_string, lambda l: lg.log(level, f'  {l}'))

        for file in local_run_dir.glob('*'):
            if file.is_file() and (file.suffix != '.root'):
                lg.log(level, f'{file.name}:')
                with file.open('r') as f:
                    _dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))


def _dump_split_string(s: str, dump: Callable[[str], None]):
    for ll in s.split('\n'):
        dump(ll)


def _extract_result_TTree(rep: cpp_ttree_rep, run_dir, output_dir: Path):
    '''Copy the final file into a place that is "safe", and return that as a path.

    The reason for this is that the temp directory we are using is about to be deleted!

    Args:
        rep (cpp_base_rep): The representation of the final result
        run_dir ([type]): Directory where it ran

    Raises:
        Exception: [description]
    '''
    current_path = run_dir / rep.filename
    new_path = output_dir / rep.filename
    shutil.copy(current_path, new_path)
    return new_path
