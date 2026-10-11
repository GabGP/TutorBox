"""Unit tests for the downloader command line and its download_models.py entry point."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.voice_models import catalog, cli, download_models

ALL_PRESENT = {"piper": True, "kokoro": True, "qwen": True}
ALL_MISSING = {"piper": False, "kokoro": False, "qwen": False}


def test_defaults_when_no_flags_are_given(monkeypatch):
    """Verifies the downloader targets the minimal tier in the default directory."""
    monkeypatch.setattr(sys, "argv", ["download_models.py"])
    arguments = cli.parse_arguments()
    assert arguments.target == "minimal"
    assert arguments.models_dir == catalog.DEFAULT_MODELS_DIR
    assert arguments.force is False
    assert arguments.check_only is False


def test_flags_are_parsed(monkeypatch, tmp_path):
    """Verifies --target, --models-dir, --force and --check-only are read."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_models.py",
            "--target",
            "qwen",
            "--models-dir",
            str(tmp_path),
            "--force",
            "--check-only",
        ],
    )
    arguments = cli.parse_arguments()
    assert arguments.target == "qwen"
    assert arguments.models_dir == tmp_path
    assert isinstance(arguments.models_dir, Path)
    assert arguments.force is True
    assert arguments.check_only is True


def test_unknown_target_is_rejected(monkeypatch):
    """Verifies an unknown --target tier makes argparse exit with code 2."""
    monkeypatch.setattr(sys, "argv", ["download_models.py", "--target", "bogus"])
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2


def test_diagnostic_marks_missing_engines(capsys):
    """Verifies the report names each engine and flags only the missing ones."""
    cli.print_diagnostic({"piper": True, "kokoro": False, "qwen": True})
    report_lines = capsys.readouterr().out.splitlines()
    assert "Utz'tutor TTS Models Diagnostic" in report_lines[1]
    assert "Piper / Sherpa (Spanish)" in report_lines[3]
    assert "Missing" not in report_lines[3]
    assert "Kokoro-82M (Multilingual)" in report_lines[4]
    assert report_lines[4].endswith("Missing")
    assert "Qwen3-TTS (GGUF Weights)" in report_lines[5]
    assert "Missing" not in report_lines[5]


@pytest.mark.parametrize(
    ("models_status", "expected_exit_code"),
    [(ALL_PRESENT, 0), (ALL_MISSING, 1)],
)
def test_check_only_exits_without_downloading(
    monkeypatch, tmp_path, models_status, expected_exit_code
):
    """Verifies --check-only exits 0 when every model is present and 1 otherwise."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_models.py", "--check-only", "--models-dir", str(tmp_path)],
    )
    with (
        patch("tools.voice_models.cli.check_models", return_value=models_status),
        patch("tools.voice_models.cli.execute_download") as mock_execute,
        pytest.raises(SystemExit) as exit_info,
    ):
        cli.main()
    assert exit_info.value.code == expected_exit_code
    mock_execute.assert_not_called()


def test_main_downloads_requested_tier(monkeypatch, tmp_path, capsys):
    """Verifies main forwards the tier, directory and force flag to the download."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_models.py",
            "--target",
            "kokoro",
            "--models-dir",
            str(tmp_path),
            "--force",
        ],
    )
    with (
        patch("tools.voice_models.cli.check_models", return_value=ALL_MISSING),
        patch(
            "tools.voice_models.cli.execute_download", return_value=True
        ) as mock_execute,
    ):
        cli.main()
    mock_execute.assert_called_once_with(
        target="kokoro", models_dir=tmp_path, force=True
    )
    console_output = capsys.readouterr().out
    assert "Downloading target tier: 'kokoro'..." in console_output
    assert "Voice model setup complete." in console_output


def test_main_exits_with_error_when_a_download_fails(monkeypatch, tmp_path, capsys):
    """Verifies a failed download makes main exit with code 1."""
    monkeypatch.setattr(
        sys, "argv", ["download_models.py", "--models-dir", str(tmp_path)]
    )
    with (
        patch("tools.voice_models.cli.check_models", return_value=ALL_MISSING),
        patch("tools.voice_models.cli.execute_download", return_value=False),
        pytest.raises(SystemExit) as exit_info,
    ):
        cli.main()
    assert exit_info.value.code == 1
    assert "One or more model downloads failed." in capsys.readouterr().out


def test_entry_point_exposes_the_cli_main():
    """Verifies download_models.py starts the voice_models command line."""
    assert download_models.main is cli.main


def test_entry_point_runs_as_a_script_from_any_directory(tmp_path):
    """Verifies the script finds tools.voice_models when started outside the repo root."""
    script_path = catalog.ROOT_DIR / "tools" / "voice_models" / "download_models.py"
    # Without the prefix exported, the script falls back to its own absolute
    # .cache/pycache instead of resolving pytest's relative one against tmp_path.
    direct_run_environment = {
        name: value
        for name, value in os.environ.items()
        if name != "PYTHONPYCACHEPREFIX"
    }
    completed = subprocess.run(
        [sys.executable, str(script_path), "--check-only", "--models-dir", "empty"],
        cwd=str(tmp_path),
        env=direct_run_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout.count("Missing") == 3
    assert completed.stderr == ""
