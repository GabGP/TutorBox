"""Verifies tool lookup and prerequisite checks for the llama-tts daemon build."""

import sys
from pathlib import Path
from unittest.mock import patch

from tools.llama_tts_daemon.build_llama import paths, toolchain
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL

PATH_CMAKE = "C:/Program Files/CMake/bin/cmake.exe"


def _touch(file_path: Path) -> Path:
    """Creates an empty file together with its parent folders."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()
    return file_path


def test_resolve_tool_returns_path_from_which_unchanged(build_tree, monkeypatch):
    """Verifies a tool found on PATH is returned as is, even if a venv copy exists."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    _touch(paths.PROJECT_VENV_DIR / "Scripts" / "cmake.exe")
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.which", return_value=PATH_CMAKE) as which_mock,
    ):
        assert toolchain.resolve_tool("cmake") == PATH_CMAKE
    which_mock.assert_called_once_with("cmake")


def test_resolve_tool_finds_active_interpreter_scripts_folder_on_windows(
    build_tree, monkeypatch
):
    """Verifies cmake.exe is found in the active interpreter's Scripts folder on Windows."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    expected = _touch(build_tree / "active" / "Scripts" / "cmake.exe")
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") == str(expected)


def test_resolve_tool_finds_active_interpreter_bin_folder_on_linux(
    build_tree, monkeypatch
):
    """Verifies cmake without an extension is found in the active interpreter's bin folder on Linux."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    expected = _touch(build_tree / "active" / "bin" / "cmake")
    with (
        patch("platform.system", return_value="Linux"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") == str(expected)


def test_resolve_tool_finds_project_venv_scripts_folder_on_windows(
    build_tree, monkeypatch
):
    """Verifies cmake.exe is found in the project venv Scripts folder on Windows."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    expected = _touch(paths.PROJECT_VENV_DIR / "Scripts" / "cmake.exe")
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") == str(expected)


def test_resolve_tool_finds_project_venv_bin_folder_on_linux(build_tree, monkeypatch):
    """Verifies cmake without an extension is found in the project venv bin folder on Linux."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    expected = _touch(paths.PROJECT_VENV_DIR / "bin" / "cmake")
    with (
        patch("platform.system", return_value="Linux"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") == str(expected)


def test_resolve_tool_prefers_active_interpreter_over_project_venv(
    build_tree, monkeypatch
):
    """Verifies the active interpreter's copy wins when the project venv has one too."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    active_copy = _touch(build_tree / "active" / "Scripts" / "cmake.exe")
    _touch(paths.PROJECT_VENV_DIR / "Scripts" / "cmake.exe")
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") == str(active_copy)


def test_resolve_tool_returns_none_when_missing_everywhere(build_tree, monkeypatch):
    """Verifies None is returned when the tool is neither on PATH nor in any venv folder."""
    monkeypatch.setattr(sys, "prefix", str(build_tree / "active"))
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.which", return_value=None),
    ):
        assert toolchain.resolve_tool("cmake") is None


def test_check_prerequisites_fails_when_git_is_missing(capsys):
    """Verifies a missing git prints the FAIL line, returns False and never looks up cmake."""
    with patch(
        "tools.llama_tts_daemon.build_llama.toolchain.resolve_tool", return_value=None
    ) as resolve_mock:
        assert toolchain.check_prerequisites() is False
    resolve_mock.assert_called_once_with("git")
    assert capsys.readouterr().out == (
        f"{TAG_FAIL} 'git' is not installed or not found in PATH.\n"
    )


def test_check_prerequisites_fails_when_cmake_is_missing(capsys):
    """Verifies a missing cmake prints the FAIL line and returns False when git is present."""
    tools_found = {"git": "/usr/bin/git", "cmake": None}
    with patch(
        "tools.llama_tts_daemon.build_llama.toolchain.resolve_tool",
        side_effect=tools_found.get,
    ):
        assert toolchain.check_prerequisites() is False
    assert capsys.readouterr().out == (
        f"{TAG_FAIL} 'cmake' is not installed or not found in PATH / virtualenv.\n"
    )


def test_check_prerequisites_passes_silently_when_both_tools_exist(capsys):
    """Verifies check_prerequisites returns True and prints nothing when git and cmake exist."""
    tools_found = {"git": "/usr/bin/git", "cmake": "/usr/bin/cmake"}
    with patch(
        "tools.llama_tts_daemon.build_llama.toolchain.resolve_tool",
        side_effect=tools_found.get,
    ):
        assert toolchain.check_prerequisites() is True
    assert capsys.readouterr().out == ""
