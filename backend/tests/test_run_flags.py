"""Unit tests for TutorBox appliance runner build, sync, and flag dispatch (run.py)."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run


def test_resolve_llama_daemon_found_in_cache():
    """Verifies resolve_llama_daemon finds cached binary under .cache/bin/llama.cpp/."""

    def fake_is_file(self):
        return "llama-tts-daemon" in self.name or "llama-tts" in self.name

    with patch("pathlib.Path.is_file", fake_is_file):
        daemon_path = run.resolve_llama_daemon()
        assert daemon_path is not None
        assert "llama.cpp" in str(daemon_path)


def test_resolve_llama_daemon_found_in_path():
    """Verifies resolve_llama_daemon finds daemon via shutil.which if not in cache."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value="/usr/local/bin/llama-tts-daemon"),
    ):
        daemon_path = run.resolve_llama_daemon()
        assert daemon_path == Path("/usr/local/bin/llama-tts-daemon").resolve()


def test_resolve_llama_daemon_missing():
    """Verifies resolve_llama_daemon returns None when daemon is absent everywhere."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value=None),
    ):
        assert run.resolve_llama_daemon() is None


def test_build_llama_success_and_force():
    """Verifies build_llama runs build_llama_tts.py with expected flags."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_run,
    ):
        assert run.build_llama(force=True) is True
        assert mock_run.call_count == 1
        assert "--force" in mock_run.call_args[0][0]


def test_build_llama_missing_script():
    """Verifies build_llama returns False when build script is missing."""
    with patch("pathlib.Path.is_file", return_value=False):
        assert run.build_llama() is False


def test_main_build_llama_flag(monkeypatch):
    """Verifies --build-llama triggers sync_backend and build_llama before check_only/uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--build-llama", "--check-only"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_llama", return_value=True) as mock_build_llama,
        patch("subprocess.run") as mock_sub,
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_build_llama.assert_called_once()
        mock_sub.assert_not_called()


def test_main_build_llama_failure_exits(monkeypatch):
    """Verifies build failure causes main to exit with code 1."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--build-llama"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_llama", return_value=False),
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    mock_sync.assert_called_once()
    assert exc_info.value.code == 1


def test_main_build_llama_no_sync_flag(monkeypatch):
    """Verifies --build-llama with --no-sync skips sync_backend."""
    monkeypatch.setattr(
        sys, "argv", ["run.py", "--build-llama", "--no-sync", "--check-only"]
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend") as mock_sync,
        patch("run.build_llama", return_value=True) as mock_build_llama,
        patch("subprocess.run") as mock_sub,
    ):
        run.main()
        mock_sync.assert_not_called()
        mock_build_llama.assert_called_once()
        mock_sub.assert_not_called()


def test_main_download_models_flag(monkeypatch):
    """Verifies --download-models triggers sync_backend before downloading."""
    monkeypatch.setattr(
        sys, "argv", ["run.py", "--download-models", "minimal", "--check-only"]
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_sub,
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "download_models.py" in str(cmd[1])
        assert "--target" in cmd
        assert "minimal" in cmd


def test_main_download_models_failure_exits(monkeypatch):
    """Verifies model download failure causes main to exit with code 1."""
    monkeypatch.setattr(
        sys, "argv", ["run.py", "--download-models", "all", "--check-only"]
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True),
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    assert exc_info.value.code == 1


def test_sync_backend_success():
    """Verifies sync_backend executes uv sync --all-extras on backend directory."""
    with patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0),
    ) as mock_sub:
        assert run.sync_backend("/mock/bin/uv") is True
        assert mock_sub.call_count == 1
        cmd = mock_sub.call_args[0][0]
        assert cmd[:3] == ["/mock/bin/uv", "sync", "--all-extras"]
        assert "--directory" in cmd
        assert "backend" in str(cmd[cmd.index("--directory") + 1])


def test_sync_backend_failure():
    """Verifies sync_backend returns False when uv sync exits with non-zero code."""
    with patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1),
    ):
        assert run.sync_backend("/mock/bin/uv") is False


def test_main_no_sync_flag(monkeypatch):
    """Verifies --no-sync skips sync_backend execution."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-sync", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend") as mock_sync,
        patch("run.build_pwa"),
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", return_value=False),
    ):
        run.main()
        mock_sync.assert_not_called()
        mock_sub.assert_called_once()


def test_main_sync_failure_exits(monkeypatch):
    """Verifies sync failure causes main to exit with code 1."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=False),
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    assert exc_info.value.code == 1
