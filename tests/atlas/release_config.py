"""
Release configuration for parameterized ATLAS AnalysisBase tests.

Maps AnalysisBase release versions to their corresponding Docker image tags.
This allows parameterized tests to run against multiple releases without
code duplication.

Example usage:
    @pytest.mark.parametrize("release_version,docker_tag", ATLAS_RELEASES)
    def test_something(release_version, docker_tag):
        local_file = AtlasXAODLocalFile(docker_tag, file_path)
        ...
"""

from typing import List, Tuple

# List of (release_version, docker_image_tag) tuples
# - release_version: Human-readable release identifier (e.g., "22.2.41")
# - docker_image_tag: Full Docker image tag (e.g., "atlas/analysisbase:22.2.96")
ATLAS_RELEASES: List[Tuple[str, str]] = [
    ("21.2.283", "gitlab-registry.cern.ch/atlas/athena/analysisbase:21.2.283"),
    ("22.2.113", "gitlab-registry.cern.ch/atlas/athena/analysisbase:22.2.113"),
    ("25.2.41", "gitlab-registry.cern.ch/atlas/athena/analysisbase:25.2.41"),
    ("25.2.79", "gitlab-registry.cern.ch/atlas/athena/analysisbase:25.2.79"),
]
