#!/usr/bin/env python3
"""Sweep engines x corpus -> CSV + blind WAVs for jury listening.

The code lives in the sweep package; this file only starts it.

Usage (repo root):
    python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper,espeak --repeats 3
    python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper --repeats 5 --out tools/benchmark/tts/results
"""

import sys
from pathlib import Path

# Run as a script, sys.path starts at this folder and bytecode would land next
# to the sources. Point both at the repo root before the package import: the
# package needs the root on sys.path, and repo policy keeps every __pycache__
# under .cache.
_ROOT_DIR = Path(__file__).resolve().parents[3]
if sys.pycache_prefix is None:
    sys.pycache_prefix = str(_ROOT_DIR / ".cache" / "pycache")
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from tools.benchmark.tts.sweep.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
