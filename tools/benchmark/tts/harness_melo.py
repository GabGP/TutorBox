#!/usr/bin/env python3
"""Standalone inference and profiling harness for MeloTTS Spanish ONNX model.

Part of Utz'tutor Phase 3 (Spike Candidate 4). The code lives in the melo
package; this file only starts it.

Usage:
    python tools/benchmark/tts/harness_melo.py --text "Hola mundo" --out tools/benchmark/tts/results/out/melo_test.wav
    python tools/benchmark/tts/harness_melo.py --profile
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

from tools.benchmark.tts.melo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
