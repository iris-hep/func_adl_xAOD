from pathlib import Path
from typing import List, Union

from func_adl_xAOD.common.local_dataset import LocalDataset
from func_adl_xAOD.cms.aod.executor import cms_aod_executor
from func_adl_xAOD.common.executor import executor


class CMSRun1AODDataset(LocalDataset):
    '''A dataset running locally
    '''
    def __init__(self,
                 files: Union[Path, str, List[Path], List[str]],
                 docker_image: str = 'cmsopendata/cmssw_5_3_32',
                 docker_tag: str = 'conddb_20210705'):
        '''Run on the given files

        Args:
            files (Path): Locally accessible files we are going to run on
            docker_image (str): The docker image name to run the executable
            docker_tag (str): The docker tag to use to run the executable
        '''
        super().__init__(files, docker_image, docker_tag)

    def get_executor_obj(self) -> executor:
        '''Return the code that will actually generate the C++ we need to execute
        here.

        Returns:
            executor: Return the executor
        '''
        return cms_aod_executor()
