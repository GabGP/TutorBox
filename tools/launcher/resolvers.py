"""Locates the external executables the Utz'tutor launcher depends on."""

import os
import shutil
import sys
from pathlib import Path

from tools.launcher.environment import resolve_venv_path
from tools.launcher.paths import LLAMA_DAEMON_CACHE_DIR


def resolve_pnpm() -> str | None:
    """Finds and returns the executable path for the pnpm package manager."""
    found = shutil.which("pnpm")
    if found:
        return found
    for fallback in [
        Path.home() / ".local" / "share" / "pnpm" / "pnpm",
        Path.home() / ".local" / "bin" / "pnpm",
        Path.home() / "AppData" / "Roaming" / "npm" / "pnpm.cmd",
    ]:
        if fallback.is_file() and (os.name == "nt" or os.access(fallback, os.X_OK)):
            return str(fallback)
    return None


def resolve_llama_daemon() -> Path | None:
    """Finds and returns the path to the llama-tts-daemon binary if available."""
    ext = ".exe" if os.name == "nt" else ""
    bin_name = f"llama-tts-daemon{ext}"
    cached = LLAMA_DAEMON_CACHE_DIR / bin_name
    if cached.is_file():
        return cached
    which_daemon = shutil.which(bin_name) or shutil.which(f"llama-tts{ext}")
    return Path(which_daemon).resolve() if which_daemon else None


def resolve_python() -> str:
    """Returns the virtualenv Python executable if available, else sys.executable."""
    venv_path = resolve_venv_path()
    ext = ".exe" if os.name == "nt" else ""
    for candidate in [
        venv_path / "Scripts" / f"python{ext}",
        venv_path / "bin" / f"python{ext}",
    ]:
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def resolve_uv() -> str:
    """Finds and returns the executable path for the uv package manager."""
    found = shutil.which("uv")
    if found:
        return found
    for fallback in [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
    ]:
        if fallback.is_file() and os.access(fallback, os.X_OK):
            return str(fallback)
    return "uv"
