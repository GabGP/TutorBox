"""Verifies the llama-tts build command line, its step order and the build.py entry point."""

import os
import subprocess
import sys
from unittest.mock import Mock, call

import pytest

from tools.llama_tts_daemon import build
from tools.llama_tts_daemon.build_llama import cli, paths
from tools.llama_tts_daemon.build_llama.console import TAG_OK


@pytest.fixture
def step_manager(monkeypatch):
    """Replaces the five build steps in cli with mocks recorded by one manager mock."""
    manager = Mock()
    step_mocks = {
        "check_prerequisites": Mock(return_value=True),
        "clone_upstream": Mock(),
        "apply_patch": Mock(),
        "build_binary": Mock(),
        "install_artifacts": Mock(),
    }
    for step_name, step_mock in step_mocks.items():
        monkeypatch.setattr(cli, step_name, step_mock)
        manager.attach_mock(step_mock, step_name)
    return manager


def test_defaults_when_no_flags_are_given(monkeypatch):
    """Verifies a run without flags keeps both the force and CPU-only switches off."""
    monkeypatch.setattr(sys, "argv", ["build.py"])
    arguments = cli.parse_arguments()
    assert arguments.force is False
    assert arguments.cpu_only is False


def test_force_and_cpu_only_flags_are_parsed(monkeypatch):
    """Verifies --force and --cpu-only switch both options on."""
    monkeypatch.setattr(sys, "argv", ["build.py", "--force", "--cpu-only"])
    arguments = cli.parse_arguments()
    assert arguments.force is True
    assert arguments.cpu_only is True


def test_unknown_flag_is_rejected(monkeypatch):
    """Verifies an unknown flag makes argparse exit with code 2."""
    monkeypatch.setattr(sys, "argv", ["build.py", "--bogus"])
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2


def test_plain_run_calls_each_step_once_in_order(monkeypatch, step_manager):
    """Verifies a run without flags calls the five build steps once each, in order."""
    monkeypatch.setattr(sys, "argv", ["build.py"])
    cli.main()
    assert step_manager.mock_calls == [
        call.check_prerequisites(),
        call.clone_upstream(force=False),
        call.apply_patch(force=False),
        call.build_binary(use_cuda=True, force=False),
        call.install_artifacts(),
    ]


def test_force_flag_is_forwarded_to_clone_patch_and_build(monkeypatch, step_manager):
    """Verifies --force reaches the clone, patch and compile steps."""
    monkeypatch.setattr(sys, "argv", ["build.py", "--force"])
    cli.main()
    assert step_manager.mock_calls == [
        call.check_prerequisites(),
        call.clone_upstream(force=True),
        call.apply_patch(force=True),
        call.build_binary(use_cuda=True, force=True),
        call.install_artifacts(),
    ]


def test_cpu_only_flag_disables_cuda_in_the_compile_step(monkeypatch, step_manager):
    """Verifies --cpu-only tells the compile step to skip CUDA."""
    monkeypatch.setattr(sys, "argv", ["build.py", "--cpu-only"])
    cli.main()
    step_manager.build_binary.assert_called_once_with(use_cuda=False, force=False)


def test_successful_run_prints_exactly_the_banner_and_completion_lines(
    monkeypatch, step_manager, capsys
):
    """Verifies a successful run prints the six console lines and nothing else."""
    monkeypatch.setattr(sys, "argv", ["build.py"])
    cli.main()
    assert capsys.readouterr().out.splitlines() == [
        "=" * 50,
        "      Utz'tutor Qwen3-TTS Daemon Build Tool        ",
        "=" * 50,
        "-" * 50,
        f"{TAG_OK} Build complete! Qwen3-TTS daemon is ready for appliance deployment.",
        "=" * 50,
    ]


def test_failed_prerequisite_check_stops_before_any_build_step(
    monkeypatch, step_manager, capsys
):
    """Verifies a failed prerequisite check exits with code 1 before any later step."""
    monkeypatch.setattr(sys, "argv", ["build.py"])
    step_manager.check_prerequisites.return_value = False
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1
    assert step_manager.mock_calls == [call.check_prerequisites()]
    assert capsys.readouterr().out.splitlines() == [
        "=" * 50,
        "      Utz'tutor Qwen3-TTS Daemon Build Tool        ",
        "=" * 50,
    ]


def test_build_module_exposes_the_cli_main():
    """Verifies build.py starts the build_llama command line."""
    assert build.main is cli.main


def test_entry_point_help_runs_as_a_script_from_any_directory(tmp_path):
    """Verifies build.py prints its help when started as a script outside the repo root."""
    script_path = paths.DAEMON_DIR / "build.py"
    # Without the prefix exported, the script falls back to its own absolute
    # .cache/pycache instead of resolving pytest's relative one against tmp_path.
    direct_run_environment = {
        name: value
        for name, value in os.environ.items()
        if name != "PYTHONPYCACHEPREFIX"
    }
    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=str(tmp_path),
        env=direct_run_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "--force" in completed.stdout
    assert "--cpu-only" in completed.stdout
    assert "Build and install Utz'tutor llama-tts daemon." in completed.stdout
    assert completed.stderr == ""
