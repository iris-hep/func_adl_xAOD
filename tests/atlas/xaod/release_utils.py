"""
Shared utilities for parameterized ATLAS xAOD tests across multiple releases.

Provides a generalized LocalFile class that accepts Docker image tags
dynamically, enabling parameterized testing across AnalysisBase releases.
"""

from pathlib import Path
from typing import Union, List

from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor
from tests.utils.base import LocalFile


class AtlasXAODDockerException(Exception):
    """Exception raised when Docker execution fails in ATLAS xAOD tests."""

    pass


class AtlasXAODLocalFile(LocalFile):
    """
    Generalized LocalFile for ATLAS xAOD that accepts dynamic Docker tags.

    This enables parameterized tests to run against different AnalysisBase releases
    without creating separate classes for each release.

    Args:
        docker_tag: Full Docker image tag (e.g., "atlas/analysisbase:22.2.96")
        local_files: Path or list of paths to local ROOT files
        source_file_name: Name of the generated C++ source file (default: "query.cxx")
    """

    def __init__(
        self,
        docker_tag: str,
        local_files: Union[Path, List[Path]],
        source_file_name: str = "query.cxx",
    ):
        super().__init__(docker_tag, source_file_name, local_files)
        self._docker_tag = docker_tag

    def raise_docker_exception(self, message: str):
        """Raise a Docker-specific exception."""
        raise AtlasXAODDockerException(message)

    def get_executor_obj(self) -> atlas_xaod_executor:
        """Get the ATLAS xAOD executor."""
        return atlas_xaod_executor()
