"""Builder for the offline classroom TTS settings section (see core/tts/espeak.py)."""

import os

from core.config.constants import (
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)
from core.config.models import TTSConfig
from core.config.parsers import parse_bool, parse_float, parse_int

__all__ = ["build_tts_config"]


def build_tts_config() -> TTSConfig:
    """Reads TTS_* environment variables and returns a typed TTSConfig instance."""
    return TTSConfig(
        enabled=parse_bool("TTS_ENABLED", DEFAULT_TTS_ENABLED),
        binary=os.environ.get("TTS_ESPEAK_BINARY", DEFAULT_TTS_BINARY).strip(),
        voice=os.environ.get("TTS_VOICE") or DEFAULT_TTS_VOICE,
        voice_quc=os.environ.get("TTS_VOICE_QUC", DEFAULT_TTS_VOICE_QUC).strip(),
        words_per_minute=parse_int(
            "TTS_WORDS_PER_MINUTE",
            DEFAULT_TTS_WORDS_PER_MINUTE,
            min_value=80,
            max_value=450,
        ),
        pitch=parse_int("TTS_PITCH", DEFAULT_TTS_PITCH, min_value=0, max_value=99),
        amplitude=parse_int(
            "TTS_AMPLITUDE", DEFAULT_TTS_AMPLITUDE, min_value=0, max_value=200
        ),
        timeout_seconds=parse_float(
            "TTS_TIMEOUT_SECONDS", DEFAULT_TTS_TIMEOUT_SECONDS, min_value=0.5
        ),
        max_chars=parse_int(
            "TTS_MAX_CHARS", DEFAULT_TTS_MAX_CHARS, min_value=40, max_value=5000
        ),
    )
