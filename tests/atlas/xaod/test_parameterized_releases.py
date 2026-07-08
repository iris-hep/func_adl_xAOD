"""
Parameterized tests for multiple ATLAS AnalysisBase releases.

These tests validate that templates, CMAKE files, and C++ code generation
work correctly across different AnalysisBase releases (R21, R22, R24, R25, etc.).

Each test is simple and lightweight, focusing on validating the build and
execution infrastructure rather than comprehensive physics analysis.

Tests are marked with atlas_releases_runner and use parameterization to run
against each configured release without code duplication.
"""

import asyncio
import logging
import os
from pathlib import Path

import pytest
from func_adl_xAOD.common.math_utils import DeltaR  # NOQA

from tests.atlas.release_config import ATLAS_RELEASES
from tests.atlas.xaod.release_utils import AtlasXAODLocalFile
from tests.atlas.r22_xaod.utils import as_pandas

# These are long tests that require Docker; only run when explicitly requested
pytestmark = pytest.mark.atlas_releases_runner

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore


@pytest.fixture(autouse=True)
def turn_on_logging():
    """Configure logging for test output."""
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)


@pytest.fixture()
def event_loop():
    """Provide event loop compatible with Windows."""
    if os.name == "nt":
        loop = asyncio.ProactorEventLoop()  # type: ignore
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()


@pytest.fixture()
def test_data_file() -> Path:
    """Provide the path to the test ROOT file.

    Uses the R22 test data which should be compatible with R22, R24, R25, etc.
    (All using similar C++ and event structure in PHYS format.)
    """
    file_path = Path(os.path.abspath("tests/atlas/r22_xaod/jets_jz1.root"))
    if not file_path.exists():
        pytest.skip(f"Test data file not found: {file_path}")
    return file_path


class TestParameterizedReleases:
    """Test suite for validating templates and CMAKE across releases.

    Each test is parameterized over ATLAS_RELEASES, running the same
    simple test against each configured release to verify template
    compatibility and CMAKE generation.
    """

    @pytest.mark.parametrize("release_version,docker_tag", ATLAS_RELEASES)
    def test_jets_count(
        self, release_version: str, docker_tag: str, test_data_file: Path
    ):
        """
        Simple test: Count total number of jets across all events.

        Validates:
        - Template rendering and CMAKE generation for the release
        - Query compilation in release-specific Docker image
        - Query execution and result collection

        The test itself is trivial (just counting), focusing on infrastructure
        rather than physics correctness.

        Args:
            release_version: Release identifier (e.g., "22.2.41")
            docker_tag: Docker image tag (e.g., "atlas/analysisbase:22.2.96")
            test_data_file: Path to test ROOT file
        """
        # Create a release-aware executor
        local_file = AtlasXAODLocalFile(docker_tag, test_data_file)

        # Run a simple query: count jets in AntiKt4EMTopoJets collection
        result_df = as_pandas(
            local_file.SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")).Select(
                lambda j: j.pt()
            )
        )

        # Verify we got a result and it's positive (should have jets in test file)
        assert result_df is not None, f"[{release_version}] Count query returned None"
        assert (
            len(result_df) > 0
        ), f"[{release_version}] Count query returned empty result"

    @pytest.mark.parametrize("release_version,docker_tag", ATLAS_RELEASES)
    def test_jets_select_pt(
        self, release_version: str, docker_tag: str, test_data_file: Path
    ):
        """
        Simple test: Extract jet pT values from events.

        Validates:
        - Template rendering for the release
        - Expression evaluation in release-specific Docker environment
        - Result collection and conversion to pandas

        Args:
            release_version: Release identifier (e.g., "22.2.41")
            docker_tag: Docker image tag (e.g., "atlas/analysisbase:22.2.96")
            test_data_file: Path to test ROOT file
        """
        # Create a release-aware executor
        local_file = AtlasXAODLocalFile(docker_tag, test_data_file)

        # Run a simple query: extract jet pT values
        result_df = as_pandas(
            local_file.SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")).Select(
                lambda j: j.pt() / 1000.0  # Convert MeV to GeV
            )
        )

        # Verify results
        assert result_df is not None, f"[{release_version}] Select query returned None"
        assert (
            len(result_df) > 0
        ), f"[{release_version}] Select query returned empty result"

        # Verify result column exists and contains numeric values
        assert (
            "col1" in result_df.columns
        ), f"[{release_version}] Expected 'col1' column in result"
        assert result_df["col1"].dtype in [
            "float64",
            "float32",
        ], f"[{release_version}] Expected numeric column, got {result_df['col1'].dtype}"

        # Verify all values are positive (pT should always be > 0)
        assert (
            result_df["col1"] > 0
        ).all(), f"[{release_version}] Expected all pT values > 0, found negative or zero value"
