"""Puts the project venv and the active interpreter's bin directories on PATH."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths


def venv_bin_dirs() -> list[str]:
    """Returns existing venv Scripts/bin dirs so pip-shimmed tools stay on PATH."""
    candidates = [
        Path(sys.prefix) / ("Scripts" if platform.system() == "Windows" else "bin"),
        paths.PROJECT_VENV_DIR / "Scripts",
        paths.PROJECT_VENV_DIR / "bin",
    ]
    seen: set[str] = set()
    dirs: list[str] = []
    for candidate_directory in candidates:
        # Resolve the dir itself (not a tool path) so cmake/ninja shims are found.
        if candidate_directory.is_dir():
            resolved = str(candidate_directory.resolve())
            if resolved not in seen:
                seen.add(resolved)
                dirs.append(resolved)
    return dirs


def env_with_venv_bins(env: dict[str, str] | None = None) -> dict[str, str]:
    """Merges os.environ with venv bin dirs prepended to PATH.

    pip packages like cmake/ninja install shims into .cache/venv/Scripts,
    which is usually NOT on PATH in a plain shell. Without this, CMake's
    find_program(ninja) fails even though resolve_tool() found the binary.
    """
    merged = dict(os.environ)
    if env:
        merged.update(env)
    path_sep = ";" if platform.system() == "Windows" else ":"
    current = merged.get("PATH", "")
    existing = [path_entry for path_entry in current.split(path_sep) if path_entry]
    existing_lower = (
        {path_entry.lower() for path_entry in existing}
        if platform.system() == "Windows"
        else set(existing)
    )
    prepend: list[str] = []
    for venv_directory in venv_bin_dirs():
        key = (
            venv_directory.lower() if platform.system() == "Windows" else venv_directory
        )
        if key not in existing_lower:
            prepend.append(venv_directory)
            existing_lower.add(key)
    if prepend:
        merged["PATH"] = path_sep.join([*prepend, *existing])
    return merged
