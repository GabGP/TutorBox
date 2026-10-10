#!/usr/bin/env python3
"""Automated Model Downloader for Utz'tutor TTS Voices.

Downloads neural acoustic models for offline classroom speech synthesis:
- Piper / Sherpa Spanish Harvard baseline (VITS, ~76 MB)
- Kokoro-82M multilingual INT8 StyleTTS2 ONNX (~140 MB compressed)
- Qwen3-TTS 1.7B Base GGUF weights & mmproj (~1.5 GB)

The steps themselves live in the sibling modules; this file only starts them.

Usage:
    python tools/voice_models/download_models.py                   # Downloads minimal tier (Piper/Sherpa Spanish)
    python tools/voice_models/download_models.py --target kokoro   # Downloads Kokoro-82M
    python tools/voice_models/download_models.py --target qwen     # Downloads Qwen3-TTS GGUF
    python tools/voice_models/download_models.py --target all      # Downloads all neural models
    python tools/voice_models/download_models.py --check-only      # Checks model status without downloading
"""

import sys
from pathlib import Path

# Run as a script, sys.path starts at this folder and bytecode would land next
# to the sources. Point both at the repo root before the tools.voice_models
# import: the package needs the root on sys.path, and repo policy keeps every
# __pycache__ under .cache (run.py already exports PYTHONPYCACHEPREFIX when it
# launches this script, so the prefix is only set here for direct runs).
_ROOT_DIR = Path(__file__).resolve().parents[2]
if sys.pycache_prefix is None:
    sys.pycache_prefix = str(_ROOT_DIR / ".cache" / "pycache")
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from tools.voice_models.cli import main

if __name__ == "__main__":
    main()
