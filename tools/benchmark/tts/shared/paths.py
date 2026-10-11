"""Locations the TTS benchmark reads from and writes to."""

from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BENCHMARK_DIR.parents[2]
BACKEND_SRC = ROOT_DIR / "backend" / "src"

DEFAULT_CORPUS_FILE = BENCHMARK_DIR / "corpus" / "es_math.txt"
DEFAULT_RESULTS_DIR = BENCHMARK_DIR / "results"
WAV_SUBDIRECTORY_NAME = "out"
DEFAULT_MELO_WAV_FILE = DEFAULT_RESULTS_DIR / WAV_SUBDIRECTORY_NAME / "melo_es_0.wav"

MELO_MODEL_DIR = ROOT_DIR / ".cache" / "models" / "tts" / "melo"
