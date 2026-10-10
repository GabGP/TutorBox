"""Unit tests for the Utz'tutor launcher executable resolvers (tools/launcher/resolvers.py)."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

from tools.launcher import resolvers


def test_resolve_pnpm_when_found():
    """Verifies resolve_pnpm returns path when pnpm is found in PATH."""
    with patch("shutil.which", return_value="/mock/bin/pnpm"):
        assert resolvers.resolve_pnpm() == "/mock/bin/pnpm"


def test_resolve_pnpm_when_missing():
    """Verifies resolve_pnpm returns None when pnpm cannot be located."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=False),
    ):
        assert resolvers.resolve_pnpm() is None


def test_resolve_pnpm_returns_fallback_when_not_on_path():
    """Verifies resolve_pnpm returns a fallback install path when PATH lookup fails."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=True),
        patch("os.access", return_value=True),
    ):
        fallback = resolvers.resolve_pnpm()
        assert fallback is not None
        assert "pnpm" in fallback


def test_resolve_uv_when_found():
    """Verifies resolve_uv returns path when uv is found in PATH."""
    with patch("shutil.which", return_value="/mock/bin/uv"):
        assert resolvers.resolve_uv() == "/mock/bin/uv"


def test_resolve_uv_fallback():
    """Verifies resolve_uv checks fallback directories if PATH lookup fails."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=True),
        patch("os.access", return_value=True),
    ):
        assert "uv" in resolvers.resolve_uv()


def test_resolve_uv_returns_bare_name_when_nothing_found():
    """Verifies resolve_uv returns the literal uv command when nothing is found."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=False),
    ):
        assert resolvers.resolve_uv() == "uv"


def test_resolve_llama_daemon_found_in_cache():
    """Verifies resolve_llama_daemon finds cached binary under .cache/bin/llama.cpp/."""

    def fake_is_file(self):
        return "llama-tts-daemon" in self.name or "llama-tts" in self.name

    with patch("pathlib.Path.is_file", fake_is_file):
        daemon_path = resolvers.resolve_llama_daemon()
        assert daemon_path is not None
        assert "llama.cpp" in str(daemon_path)


def test_resolve_llama_daemon_found_in_path():
    """Verifies resolve_llama_daemon finds daemon via shutil.which if not in cache."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value="/usr/local/bin/llama-tts-daemon"),
    ):
        daemon_path = resolvers.resolve_llama_daemon()
        assert daemon_path == Path("/usr/local/bin/llama-tts-daemon").resolve()


def test_resolve_llama_daemon_missing():
    """Verifies resolve_llama_daemon returns None when daemon is absent everywhere."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value=None),
    ):
        assert resolvers.resolve_llama_daemon() is None


def test_resolve_python_when_found(tmp_path, monkeypatch):
    """Verifies resolve_python returns virtualenv python when present."""
    scripts_dir = tmp_path / ("Scripts" if os.name == "nt" else "bin")
    scripts_dir.mkdir(parents=True)
    ext = ".exe" if os.name == "nt" else ""
    py_bin = scripts_dir / f"python{ext}"
    py_bin.write_text("")
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(tmp_path))
    assert resolvers.resolve_python() == str(py_bin)


def test_resolve_python_falls_back_to_sys_executable(tmp_path, monkeypatch):
    """Verifies resolve_python returns sys.executable when the venv has no interpreter."""
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(tmp_path))
    assert resolvers.resolve_python() == sys.executable
