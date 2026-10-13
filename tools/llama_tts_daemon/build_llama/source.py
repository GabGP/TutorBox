"""Clones the pinned upstream llama.cpp and applies the llama-tts patches in order."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.commands import run_cmd
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL, TAG_INFO, TAG_OK

PINNED_TAG = "b11002"
UPSTREAM_REPO = "https://github.com/ggerganov/llama.cpp.git"


def clone_upstream(force: bool = False) -> None:
    """Clones upstream llama.cpp repository pinned to release b11002."""
    if force and paths.SOURCE_DIR.exists():
        print(
            f"{TAG_INFO} Removing existing build directory for clean rebuild: {paths.SOURCE_DIR}"
        )
        shutil.rmtree(paths.SOURCE_DIR, ignore_errors=True)

    if not (paths.SOURCE_DIR / ".git").is_dir():
        print(f"{TAG_INFO} Cloning {UPSTREAM_REPO} (tag: {PINNED_TAG})...")
        paths.SOURCE_DIR.parent.mkdir(parents=True, exist_ok=True)
        run_cmd(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                PINNED_TAG,
                UPSTREAM_REPO,
                str(paths.SOURCE_DIR),
            ]
        )
    else:
        print(f"{TAG_OK} Upstream repository already present at {paths.SOURCE_DIR}")


def apply_patch(patch_file: Path, force: bool = False) -> None:
    """Applies one patch onto upstream llama.cpp, unless it is already applied."""
    if not patch_file.is_file():
        print(f"{TAG_FAIL} Patch file not found at {patch_file}")
        sys.exit(1)

    # Check if patch is already applied
    res = subprocess.run(
        [
            "git",
            "-C",
            str(paths.SOURCE_DIR),
            "apply",
            "--whitespace=nowarn",
            "--reverse",
            "--check",
            str(patch_file),
        ],
        capture_output=True,
        check=False,
    )
    if res.returncode == 0 and not force:
        print(f"{TAG_OK} Patch already applied: {patch_file.name}")
        return

    print(f"{TAG_INFO} Applying patch: {patch_file.name}...")
    run_cmd(
        [
            "git",
            "-C",
            str(paths.SOURCE_DIR),
            "apply",
            "--whitespace=nowarn",
            str(patch_file),
        ]
    )
    print(f"{TAG_OK} Applied patch: {patch_file.name}")


def apply_patches(force: bool = False) -> None:
    """Applies every patch in paths.PATCH_FILES, in order, onto upstream llama.cpp."""
    for patch_file in paths.PATCH_FILES:
        apply_patch(patch_file, force=force)
