"""Unit tests for the run.py entry point: env loading, flag dispatch and launch order."""

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

import run
from tools.launcher import paths


@pytest.fixture(autouse=True)
def _isolated_launcher_environment(monkeypatch):
    """Stops main() from loading real .env files or leaking UV_PROJECT_ENVIRONMENT."""
    monkeypatch.setattr(run, "load_env", lambda env_path: None)
    monkeypatch.setenv(
        "UV_PROJECT_ENVIRONMENT", os.environ.get("UV_PROJECT_ENVIRONMENT", "")
    )


def test_main_check_only(monkeypatch):
    """Verifies that --check-only halts before running build or uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--check-only"])
    with (
        patch("run.check_prerequisites") as mock_check,
        patch("run.build_pwa") as mock_build,
        patch("subprocess.run") as mock_sub,
    ):
        run.main()
        mock_check.assert_called_once()
        mock_build.assert_not_called()
        mock_sub.assert_not_called()


def test_main_no_build(monkeypatch):
    """Verifies that --no-build skips PWA build step and launches uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])

    def fake_is_file(self):
        return self.name == "logging_config.json"

    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa") as mock_build,
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", fake_is_file),
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_build.assert_not_called()
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "--log-config" in cmd


def test_main_omits_log_config_when_missing(monkeypatch):
    """Verifies --log-config is omitted when logging_config.json is absent."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa"),
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", return_value=False),
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "--log-config" not in cmd


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


def test_main_loads_root_then_backend_env_files(monkeypatch):
    """Verifies main loads the root .env first and the backend .env second."""
    mock_load_env = MagicMock()
    monkeypatch.setattr(run, "load_env", mock_load_env)
    monkeypatch.setattr(sys, "argv", ["run.py", "--check-only"])
    with patch("run.check_prerequisites"):
        run.main()
    assert [call.args[0] for call in mock_load_env.call_args_list] == [
        paths.ROOT_DIR / ".env",
        paths.BACKEND_DIR / ".env",
    ]


def test_main_forwards_host_port_and_reload_to_serve(monkeypatch):
    """Verifies --host, --port and --no-reload reach serve() unchanged."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "--host",
            "127.0.0.1",
            "--port",
            "9001",
            "--no-reload",
            "--no-sync",
            "--no-build",
        ],
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.resolve_uv", return_value="/mock/uv"),
        patch("run.serve") as mock_serve,
    ):
        run.main()
    mock_serve.assert_called_once_with(
        "/mock/uv", host="127.0.0.1", port=9001, reload=False
    )


def test_default_run_builds_pwa_and_serves_with_reload(monkeypatch):
    """Verifies a default run syncs, builds the PWA and serves with auto-reload."""
    monkeypatch.setattr(sys, "argv", ["run.py"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True),
        patch("run.build_pwa") as mock_build,
        patch("run.serve") as mock_serve,
    ):
        run.main()
    mock_build.assert_called_once()
    mock_serve.assert_called_once()
    assert mock_serve.call_args.kwargs["reload"] is True


def test_main_stores_absolute_uv_project_environment(monkeypatch):
    """Verifies main rewrites a relative UV_PROJECT_ENVIRONMENT to an absolute path."""
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "custom/venv")
    monkeypatch.setattr(sys, "argv", ["run.py", "--check-only"])
    with patch("run.check_prerequisites"):
        run.main()
    assert os.path.isabs(os.environ["UV_PROJECT_ENVIRONMENT"])


def test_check_only_never_syncs_backend(monkeypatch):
    """Verifies --check-only alone skips the backend dependency sync."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--check-only"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend") as mock_sync,
    ):
        run.main()
    mock_sync.assert_not_called()
