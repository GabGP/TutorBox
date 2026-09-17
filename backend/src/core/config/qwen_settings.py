"""Environment parsing for the Qwen3-TTS runtime options."""

import os

from core.config.constants import (
    DEFAULT_TTS_QWEN_BINARY,
    DEFAULT_TTS_QWEN_CONTEXT,
    DEFAULT_TTS_QWEN_GGUF_PATH,
    DEFAULT_TTS_QWEN_SEED,
    DEFAULT_TTS_QWEN_SPEAKER_FILE,
    DEFAULT_TTS_QWEN_THREADS,
)
from core.config.parsers import parse_int

__all__ = ["build_qwen_config"]


def build_qwen_config() -> dict[str, object]:
    """Reads the Qwen-specific TTS environment variables."""
    env = os.environ.get
    return {
        "qwen_binary": env("TTS_QWEN_BINARY", DEFAULT_TTS_QWEN_BINARY).strip(),
        "qwen_gguf_path": env("TTS_QWEN_GGUF_PATH", DEFAULT_TTS_QWEN_GGUF_PATH).strip(),
        "qwen_threads": parse_int(
            "TTS_QWEN_THREADS", DEFAULT_TTS_QWEN_THREADS, min_value=1, max_value=16
        ),
        "qwen_context": parse_int(
            "TTS_QWEN_CONTEXT",
            DEFAULT_TTS_QWEN_CONTEXT,
            min_value=512,
            max_value=32768,
        ),
        "qwen_seed": parse_int("TTS_QWEN_SEED", DEFAULT_TTS_QWEN_SEED, min_value=-1),
        "qwen_speaker_file": env(
            "TTS_QWEN_SPEAKER_FILE", DEFAULT_TTS_QWEN_SPEAKER_FILE
        ).strip(),
    }
