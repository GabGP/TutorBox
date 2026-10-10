"""Runs build subprocesses inside the MSVC and venv environment they need."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL
from tools.llama_tts_daemon.build_llama.environment import env_with_venv_bins
from tools.llama_tts_daemon.build_llama.msvc import find_vcvars64


def run_cmd(
    cmd: list[str] | str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Executes a subprocess command, wrapping in vcvars64.bat on Windows when needed."""
    is_windows = platform.system() == "Windows"
    vcvars = find_vcvars64() if is_windows else None
    merged_env = env_with_venv_bins(env)

    if is_windows and vcvars:
        # list2cmdline quotes args containing spaces (e.g. under Program Files).
        cmd_str = subprocess.list2cmdline(cmd) if isinstance(cmd, list) else cmd
        full_cmd = f'cmd /c "call "{vcvars}" && {cmd_str}"'
        res = subprocess.run(
            full_cmd,
            cwd=str(cwd or paths.ROOT_DIR),
            env=merged_env,
            shell=True,
            check=False,
        )
    else:
        res = subprocess.run(
            cmd, cwd=str(cwd or paths.ROOT_DIR), env=merged_env, check=False
        )

    if res.returncode != 0:
        print(f"{TAG_FAIL} Command failed with exit code {res.returncode}: {cmd}")
        sys.exit(res.returncode)
