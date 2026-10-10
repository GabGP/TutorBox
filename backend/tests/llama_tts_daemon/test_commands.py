"""Unit tests for the build subprocess runner (tools/llama_tts_daemon/build_llama/commands.py)."""

import subprocess
from unittest.mock import patch

import pytest

from tools.llama_tts_daemon.build_llama import commands, paths
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL

VCVARS_PATH = "C:/VS/VC/Auxiliary/Build/vcvars64.bat"
MERGED_ENV = {"PATH": "x"}


@pytest.fixture
def mocked_subprocess_run():
    """Replaces subprocess.run with a mock that reports success by default."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        yield mock_run


@pytest.fixture
def mocked_vcvars_lookup():
    """Replaces find_vcvars64 with a mock that finds no vcvars64.bat by default."""
    with patch(
        "tools.llama_tts_daemon.build_llama.commands.find_vcvars64",
        return_value=None,
    ) as mock_lookup:
        yield mock_lookup


@pytest.fixture
def mocked_env_merge():
    """Replaces env_with_venv_bins with a mock that returns a fixed environment."""
    with patch(
        "tools.llama_tts_daemon.build_llama.commands.env_with_venv_bins",
        return_value=MERGED_ENV,
    ) as mock_merge:
        yield mock_merge


@pytest.fixture
def project_root_in_tmp(tmp_path, monkeypatch):
    """Points paths.ROOT_DIR at tmp_path so the default working directory is harmless."""
    monkeypatch.setattr(paths, "ROOT_DIR", tmp_path)
    return tmp_path


def test_run_cmd_on_linux_passes_list_unchanged(
    project_root_in_tmp,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that on Linux a list command runs unchanged with no shell and without consulting vcvars64."""
    command = ["git", "status"]

    with patch("platform.system", return_value="Linux"):
        commands.run_cmd(command)

    mocked_vcvars_lookup.assert_not_called()
    mocked_subprocess_run.assert_called_once_with(
        command, cwd=str(project_root_in_tmp), env=MERGED_ENV, check=False
    )


def test_run_cmd_uses_explicit_cwd_as_string(
    tmp_path,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that an explicit cwd argument is forwarded to subprocess.run as a string."""
    source_directory = tmp_path / "llama.cpp"

    with patch("platform.system", return_value="Linux"):
        commands.run_cmd(["git", "status"], cwd=source_directory)

    mocked_subprocess_run.assert_called_once_with(
        ["git", "status"], cwd=str(source_directory), env=MERGED_ENV, check=False
    )


def test_run_cmd_forwards_env_to_env_with_venv_bins(
    project_root_in_tmp,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that the env argument is handed to env_with_venv_bins and the merged result is used."""
    caller_env = {"CUDA_PATH": "C:/cuda"}

    with patch("platform.system", return_value="Linux"):
        commands.run_cmd(["git", "status"], env=caller_env)

    mocked_env_merge.assert_called_once_with(caller_env)
    assert mocked_subprocess_run.call_args.kwargs["env"] == MERGED_ENV


def test_run_cmd_on_windows_wraps_list_command_in_vcvars(
    project_root_in_tmp,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that on Windows a list command is joined with list2cmdline, quoted, and run through the vcvars64 wrapper."""
    mocked_vcvars_lookup.return_value = VCVARS_PATH
    command = ["cmake", "--build", "C:/Program Files/build dir"]

    with patch("platform.system", return_value="Windows"):
        commands.run_cmd(command)

    expected_full_command = (
        f'cmd /c "call "{VCVARS_PATH}" && {subprocess.list2cmdline(command)}"'
    )
    mocked_subprocess_run.assert_called_once_with(
        expected_full_command,
        cwd=str(project_root_in_tmp),
        env=MERGED_ENV,
        shell=True,
        check=False,
    )


def test_run_cmd_on_windows_embeds_string_command_as_is(
    project_root_in_tmp,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that on Windows a string command is embedded in the vcvars64 wrapper without re-quoting."""
    mocked_vcvars_lookup.return_value = VCVARS_PATH

    with patch("platform.system", return_value="Windows"):
        commands.run_cmd("ninja -C build")

    mocked_subprocess_run.assert_called_once_with(
        f'cmd /c "call "{VCVARS_PATH}" && ninja -C build"',
        cwd=str(project_root_in_tmp),
        env=MERGED_ENV,
        shell=True,
        check=False,
    )


def test_run_cmd_on_windows_without_vcvars_runs_plain_command(
    project_root_in_tmp,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that on Windows with no vcvars64.bat found the command runs plainly, with no shell keyword."""
    command = ["git", "status"]

    with patch("platform.system", return_value="Windows"):
        commands.run_cmd(command)

    mocked_vcvars_lookup.assert_called_once_with()
    mocked_subprocess_run.assert_called_once_with(
        command, cwd=str(project_root_in_tmp), env=MERGED_ENV, check=False
    )


def test_run_cmd_prints_failure_and_exits_with_child_code(
    project_root_in_tmp,
    capsys,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that a non-zero return code prints a FAIL line naming the command and exits with that code."""
    mocked_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=3
    )
    command = ["git", "clone"]

    with (
        patch("platform.system", return_value="Linux"),
        pytest.raises(SystemExit) as exit_info,
    ):
        commands.run_cmd(command)

    assert exit_info.value.code == 3
    assert (
        capsys.readouterr().out
        == f"{TAG_FAIL} Command failed with exit code 3: {command}\n"
    )


def test_run_cmd_is_silent_and_returns_none_on_success(
    project_root_in_tmp,
    capsys,
    mocked_subprocess_run,
    mocked_vcvars_lookup,
    mocked_env_merge,
):
    """Verifies that a zero return code returns None and prints nothing."""
    with patch("platform.system", return_value="Linux"):
        result = commands.run_cmd(["git", "status"])

    assert result is None
    assert capsys.readouterr().out == ""
