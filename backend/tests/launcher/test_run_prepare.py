"""Unit tests for run.py --prepare (build, then exit) and the --require-cuda hand-off."""

import os
import sys
from unittest.mock import patch

import pytest

import run


@pytest.fixture(autouse=True)
def _isolated_launcher_environment(monkeypatch):
    """Stops main() from loading real .env files or leaking UV_PROJECT_ENVIRONMENT."""
    monkeypatch.setattr(run, "load_env", lambda env_path: None)
    monkeypatch.setenv(
        "UV_PROJECT_ENVIRONMENT", os.environ.get("UV_PROJECT_ENVIRONMENT", "")
    )


def test_prepare_builds_everything_and_never_serves(monkeypatch):
    """Verifies --prepare syncs and builds the PWA, then returns without starting the server."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--prepare"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa", return_value=True) as mock_build,
        patch("run.serve") as mock_serve,
    ):
        run.main()
    mock_sync.assert_called_once()
    mock_build.assert_called_once()
    mock_serve.assert_not_called()


def test_prepare_exits_when_the_pwa_is_not_built(monkeypatch):
    """Verifies --prepare exits with code 1 when the PWA build fails."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--prepare"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True),
        patch("run.build_pwa", return_value=False),
        patch("run.serve") as mock_serve,
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    assert exc_info.value.code == 1
    mock_serve.assert_not_called()


def test_failed_pwa_build_still_serves_without_prepare(monkeypatch):
    """Verifies a normal run serves the API even when the PWA build fails."""
    monkeypatch.setattr(sys, "argv", ["run.py"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True),
        patch("run.build_pwa", return_value=False),
        patch("run.serve") as mock_serve,
    ):
        run.main()
    mock_serve.assert_called_once()


def test_prepare_with_no_build_skips_the_pwa(monkeypatch):
    """Verifies --prepare --no-build syncs only and returns without serving."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--prepare", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa") as mock_build,
        patch("run.serve") as mock_serve,
    ):
        run.main()
    mock_sync.assert_called_once()
    mock_build.assert_not_called()
    mock_serve.assert_not_called()


@pytest.mark.parametrize(
    ("extra_flags", "expected_require_cuda"),
    [([], False), (["--require-cuda"], True)],
)
def test_require_cuda_reaches_the_daemon_build(
    monkeypatch, extra_flags, expected_require_cuda
):
    """Verifies --require-cuda is forwarded to build_llama, and is off without the flag."""
    monkeypatch.setattr(
        sys, "argv", ["run.py", "--build-llama", "--check-only", *extra_flags]
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True),
        patch("run.resolve_python", return_value="/mock/python"),
        patch("run.build_llama", return_value=True) as mock_build_llama,
    ):
        run.main()
    mock_build_llama.assert_called_once_with(
        force=False, python_bin="/mock/python", require_cuda=expected_require_cuda
    )
