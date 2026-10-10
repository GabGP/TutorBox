"""Discards a CMake build folder whose cache no longer matches the chosen generator."""

from __future__ import annotations

import shutil

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.console import TAG_INFO

NINJA_GENERATOR_MARKER = "CMAKE_GENERATOR:INTERNAL=Ninja"
MISSING_MAKE_PROGRAM_MARKER = "CMAKE_MAKE_PROGRAM:FILEPATH=CMAKE_MAKE_PROGRAM-NOTFOUND"


def discard_stale_cache(has_ninja: bool) -> None:
    """Removes the CMake build folder when its cache no longer matches the chosen generator."""
    cmake_cache = paths.BUILD_DIR / "CMakeCache.txt"
    if not cmake_cache.is_file():
        return
    cache_content = cmake_cache.read_text(encoding="utf-8", errors="ignore")
    existing_generator = "Ninja" if NINJA_GENERATOR_MARKER in cache_content else "Other"
    desired_generator = "Ninja" if has_ninja else "Other"
    stale_ninja = MISSING_MAKE_PROGRAM_MARKER in cache_content
    if existing_generator != desired_generator or (stale_ninja and has_ninja):
        reason = (
            "stale CMAKE_MAKE_PROGRAM-NOTFOUND with ninja now resolvable"
            if stale_ninja and has_ninja and existing_generator == desired_generator
            else f"Generator changed from {existing_generator} to {desired_generator}"
        )
        print(f"{TAG_INFO} {reason}. Cleaning build cache...")
        shutil.rmtree(paths.BUILD_DIR, ignore_errors=True)
