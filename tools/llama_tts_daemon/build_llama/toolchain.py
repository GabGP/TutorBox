"""Finds the git and cmake build tools on the host or inside a Python virtualenv."""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL


def resolve_tool(name: str) -> str | None:
    """Finds a tool in PATH or inside the active Python virtual environment."""
    found = shutil.which(name)
    if found:
        return found
    ext = ".exe" if platform.system() == "Windows" else ""
    venv_bins = [
        Path(sys.prefix) / "Scripts" / f"{name}{ext}",
        Path(sys.prefix) / "bin" / f"{name}{ext}",
        paths.PROJECT_VENV_DIR / "Scripts" / f"{name}{ext}",
        paths.PROJECT_VENV_DIR / "bin" / f"{name}{ext}",
    ]
    for candidate_path in venv_bins:
        if candidate_path.is_file():
            return str(candidate_path)
    return None


def check_prerequisites() -> bool:
    """Verifies that git and cmake are installed on the host or in virtualenv."""
    if not resolve_tool("git"):
        print(f"{TAG_FAIL} 'git' is not installed or not found in PATH.")
        return False
    if not resolve_tool("cmake"):
        print(f"{TAG_FAIL} 'cmake' is not installed or not found in PATH / virtualenv.")
        return False
    return True
