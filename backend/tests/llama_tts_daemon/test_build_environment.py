"""Unit tests for venv bin discovery and PATH merging (tools/llama_tts_daemon/build_llama/environment.py)."""

import os
import sys
from unittest.mock import patch

from tools.llama_tts_daemon.build_llama import environment, paths

VENV_BIN_DIRS_TARGET = "tools.llama_tts_daemon.build_llama.environment.venv_bin_dirs"


def test_venv_bin_dirs_returns_empty_list_when_no_directory_exists(
    build_tree, monkeypatch
):
    """Verifies venv_bin_dirs returns an empty list when none of the candidate directories exist."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))

    with patch("platform.system", return_value="Windows"):
        assert environment.venv_bin_dirs() == []


def test_venv_bin_dirs_looks_in_prefix_scripts_on_windows(build_tree, monkeypatch):
    """Verifies that on Windows venv_bin_dirs returns the active interpreter's Scripts directory and ignores bin."""
    active_prefix = build_tree / "active"
    monkeypatch.setattr(sys, "prefix", str(active_prefix))
    (active_prefix / "Scripts").mkdir(parents=True)
    (active_prefix / "bin").mkdir()

    with patch("platform.system", return_value="Windows"):
        directories = environment.venv_bin_dirs()

    assert directories == [str((active_prefix / "Scripts").resolve())]


def test_venv_bin_dirs_looks_in_prefix_bin_on_linux(build_tree, monkeypatch):
    """Verifies that on Linux venv_bin_dirs returns the active interpreter's bin directory and ignores Scripts."""
    active_prefix = build_tree / "active"
    monkeypatch.setattr(sys, "prefix", str(active_prefix))
    (active_prefix / "bin").mkdir(parents=True)
    (active_prefix / "Scripts").mkdir()

    with patch("platform.system", return_value="Linux"):
        directories = environment.venv_bin_dirs()

    assert directories == [str((active_prefix / "bin").resolve())]


def test_venv_bin_dirs_returns_shared_project_directory_once(build_tree, monkeypatch):
    """Verifies that when sys.prefix is the project venv, its Scripts directory is listed once, followed by bin."""
    project_venv = paths.PROJECT_VENV_DIR
    monkeypatch.setattr(sys, "prefix", str(project_venv))
    (project_venv / "Scripts").mkdir(parents=True)
    (project_venv / "bin").mkdir()

    with patch("platform.system", return_value="Windows"):
        directories = environment.venv_bin_dirs()

    assert directories == [
        str((project_venv / "Scripts").resolve()),
        str((project_venv / "bin").resolve()),
    ]


def test_venv_bin_dirs_orders_active_interpreter_before_project_venv(
    build_tree, monkeypatch
):
    """Verifies the order is active interpreter bin, then project Scripts, then project bin when all exist."""
    active_prefix = build_tree / "active"
    project_venv = paths.PROJECT_VENV_DIR
    monkeypatch.setattr(sys, "prefix", str(active_prefix))
    expected_directories = [
        active_prefix / "bin",
        project_venv / "Scripts",
        project_venv / "bin",
    ]
    for expected_directory in expected_directories:
        expected_directory.mkdir(parents=True)

    with patch("platform.system", return_value="Linux"):
        directories = environment.venv_bin_dirs()

    assert directories == [
        str(directory.resolve()) for directory in expected_directories
    ]


def test_env_with_venv_bins_prepends_venv_dirs_with_colon_on_linux(monkeypatch):
    """Verifies that on Linux the venv directories are prepended to PATH joined with colons."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["/venv/bin"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == "/venv/bin:/usr/bin:/bin"


def test_env_with_venv_bins_joins_with_semicolon_on_windows(monkeypatch):
    """Verifies that on Windows the venv directories are prepended to PATH joined with semicolons."""
    monkeypatch.setenv("PATH", "C:\\Windows\\System32")

    with (
        patch("platform.system", return_value="Windows"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["C:\\venv\\Scripts"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == "C:\\venv\\Scripts;C:\\Windows\\System32"


def test_env_with_venv_bins_ignores_case_difference_on_windows(monkeypatch):
    """Verifies that on Windows a venv directory already on PATH in another letter case is not prepended again."""
    original_path = "c:\\VENV\\scripts;C:\\Windows\\System32"
    monkeypatch.setenv("PATH", original_path)

    with (
        patch("platform.system", return_value="Windows"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["C:\\venv\\Scripts"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == original_path


def test_env_with_venv_bins_is_case_sensitive_on_linux(monkeypatch):
    """Verifies that on Linux a venv directory differing only in letter case is still prepended."""
    monkeypatch.setenv("PATH", "/VENV/bin:/usr/bin")

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["/venv/bin"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == "/venv/bin:/VENV/bin:/usr/bin"


def test_env_with_venv_bins_leaves_path_unchanged_when_all_dirs_present(monkeypatch):
    """Verifies PATH is left exactly as it was when every venv directory is already on it."""
    original_path = "/usr/bin:/venv/bin"
    monkeypatch.setenv("PATH", original_path)

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["/venv/bin"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == original_path


def test_env_with_venv_bins_merges_env_over_os_environ_without_mutating_it(monkeypatch):
    """Verifies the env argument overrides os.environ, other keys are kept, and os.environ is not changed."""
    monkeypatch.setenv("LLAMA_BUILD_TEST_OVERRIDE", "from-os")
    monkeypatch.setenv("LLAMA_BUILD_TEST_KEPT", "kept")

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=[]),
    ):
        merged = environment.env_with_venv_bins(
            {"LLAMA_BUILD_TEST_OVERRIDE": "from-env"}
        )

    assert merged["LLAMA_BUILD_TEST_OVERRIDE"] == "from-env"
    assert merged["LLAMA_BUILD_TEST_KEPT"] == "kept"
    assert merged is not os.environ
    assert os.environ["LLAMA_BUILD_TEST_OVERRIDE"] == "from-os"


def test_env_with_venv_bins_handles_empty_path(monkeypatch):
    """Verifies an empty PATH ends up containing only the venv directories."""
    monkeypatch.setenv("PATH", "")

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["/venv/bin"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == "/venv/bin"


def test_env_with_venv_bins_handles_missing_path(monkeypatch):
    """Verifies a PATH that is not set at all ends up containing only the venv directories."""
    monkeypatch.delenv("PATH", raising=False)

    with (
        patch("platform.system", return_value="Linux"),
        patch(VENV_BIN_DIRS_TARGET, return_value=["/venv/bin"]),
    ):
        merged = environment.env_with_venv_bins()

    assert merged["PATH"] == "/venv/bin"
