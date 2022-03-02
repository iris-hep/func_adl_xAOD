from pathlib import Path
from typing import List, Optional, Union

from func_adl_xAOD.common.local_dataset import LocalDataset, docker_volume_info
from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor
from func_adl_xAOD.common.executor import executor


class xAODDataset(LocalDataset):
    '''A dataset running locally
    '''
    def __init__(self,
                 files: Union[Path, str, List[Path], List[str]],
                 docker_image: str = 'atlas/analysisbase',
                 docker_tag: str = '21.2.197',
                 output_directory: Optional[Path] = None):
        '''Run on the given files

        Args:
            files (Path): Locally accessible files we are going to run on
            docker_image (str): The docker image name to run the executable
            docker_tag (str): The docker tag to use to run the executable

        Note:
            * (R21 Release Notes)[https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/AnalysisBaseReleaseNotes21_2]
        '''
        super().__init__(files, docker_image, docker_tag, output_directory)

    def get_executor_obj(self) -> executor:
        '''Return the code that will actually generate the C++ we need to execute
        here.

        Returns:
            executor: Return the executor
        '''
        return atlas_xaod_executor()

    def docker_cache_volume(self) -> List[docker_volume_info]:
        return [docker_volume_info(docker_name='atlas_xaod_calibration_cache', mount_point='/xaod_calibration_cache')]
