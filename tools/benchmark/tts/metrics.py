#!/usr/bin/env python3
"""Single-run TTS diagnostic profiler: latency, RTF, sample rate and peak level.

Synthesizes one sentence through the backend TTS router and prints its metrics.
The code lives in the profiling package; this file only starts it.

Usage:
    python tools/benchmark/tts/metrics.py --engine piper
    python tools/benchmark/tts/metrics.py --engine qwen3-tts --text "Hola mundo"

From Python:
    from tools.benchmark.tts import profile_engine, profile_speech_synthesis

    result = profile_speech_synthesis("Hola mundo", lang="es")
    stats = profile_engine("piper", "Hola mundo", repeats=3)
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

from tools.benchmark.tts.profiling.cli import main

if __name__ == "__main__":
    main()
