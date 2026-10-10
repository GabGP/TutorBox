"""Puts the repository root on sys.path and offers a temporary build tree."""

import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.llama_tts_daemon.build_llama import paths


@pytest.fixture
def build_tree(tmp_path, monkeypatch):
    """Redirects every build location to tmp_path; no directory is created."""
    source_directory = tmp_path / "source"
    daemon_directory = tmp_path / "daemon"
    monkeypatch.setattr(paths, "SOURCE_DIR", source_directory)
    monkeypatch.setattr(paths, "BUILD_DIR", source_directory / "build")
    monkeypatch.setattr(paths, "CACHE_BIN_DIR", tmp_path / "bin")
    monkeypatch.setattr(
        paths, "PATCH_FILE", daemon_directory / "0001-llama-tts-daemon-mode.patch"
    )
    monkeypatch.setattr(paths, "LICENSE_SRC", daemon_directory / "LICENSE-llama-cpp")
    monkeypatch.setattr(paths, "PROJECT_VENV_DIR", tmp_path / "venv")
    return tmp_path
