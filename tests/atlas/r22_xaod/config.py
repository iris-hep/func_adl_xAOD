import os
from pathlib import Path

import pytest

from .utils import AtlasXAODR22LocalFile

# This mark should be turned off if we want to run long-running tests.
run_long_running_tests = pytest.mark.atlas_r22_xaod_runner

# The file we can use in our test. It has only 10 events...
local_path = "tests/atlas/r22_xaod/jets_jz1.root"
f_location = Path(os.path.abspath(local_path))
f_single = AtlasXAODR22LocalFile(f_location)
f_multiple = AtlasXAODR22LocalFile([f_location, f_location])
