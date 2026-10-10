#!/usr/bin/env python3
"""Automated Build & Patch Tool for Utz'tutor Qwen3-TTS Daemon.

Clones pinned upstream llama.cpp (b11002), applies the persistent daemon patch
(0001-llama-tts-daemon-mode.patch), compiles the binary with CUDA or CPU,
and installs llama-tts-daemon into .cache/bin/llama.cpp/ alongside its MIT license.

The steps themselves live in the build_llama package; this file only starts them.

Usage:
    python tools/llama_tts_daemon/build.py
    python tools/llama_tts_daemon/build.py --force
    python tools/llama_tts_daemon/build.py --cpu-only
"""

import sys
from pathlib import Path

# Run as a script, sys.path starts at this folder and bytecode would land next
# to the sources. Point both at the repo root before the build_llama import:
# the package needs the root on sys.path, and repo policy keeps every
# __pycache__ under .cache (run.py already exports PYTHONPYCACHEPREFIX when it
# launches this script, so the prefix is only set here for direct runs).
_ROOT_DIR = Path(__file__).resolve().parents[2]
if sys.pycache_prefix is None:
    sys.pycache_prefix = str(_ROOT_DIR / ".cache" / "pycache")
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from tools.llama_tts_daemon.build_llama.cli import main

if __name__ == "__main__":
    main()
