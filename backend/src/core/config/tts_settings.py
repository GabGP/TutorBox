"""Builder for the offline classroom TTS settings section (see core/tts/)."""

import os

from core.config.constants import (
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_PIPER_BINARY,
    DEFAULT_TTS_PIPER_LENGTH_SCALE,
    DEFAULT_TTS_PIPER_MODEL_DIR,
    DEFAULT_TTS_PIPER_MODEL_ES,
    DEFAULT_TTS_PIPER_MODEL_QUC,
    DEFAULT_TTS_PIPER_NOISE_SCALE,
    DEFAULT_TTS_PIPER_NOISE_W_SCALE,
    DEFAULT_TTS_PIPER_SPEAKER_ES,
    DEFAULT_TTS_PIPER_SPEAKER_QUC,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)
from core.config.models import TTSConfig
from core.config.parsers import parse_bool, parse_float, parse_int

__all__ = ["build_tts_config"]

_VALID_ENGINES: frozenset[str] = frozenset({"auto", "piper", "espeak"})


def _parse_engine(env_var: str = "TTS_ENGINE") -> str:
    """Parses TTS_ENGINE and falls back to auto if unconfigured or invalid."""
    raw = os.environ.get(env_var, "").strip().lower()
    return raw if raw in _VALID_ENGINES else DEFAULT_TTS_ENGINE


def build_tts_config() -> TTSConfig:
    """Reads TTS_* environment variables and returns a typed TTSConfig instance."""
    return TTSConfig(
        enabled=parse_bool("TTS_ENABLED", DEFAULT_TTS_ENABLED),
        engine=_parse_engine("TTS_ENGINE"),
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
        piper_binary=os.environ.get(
            "TTS_PIPER_BINARY", DEFAULT_TTS_PIPER_BINARY
        ).strip(),
        piper_model_dir=os.environ.get(
            "TTS_PIPER_MODEL_DIR", DEFAULT_TTS_PIPER_MODEL_DIR
        ).strip(),
        piper_model_es=os.environ.get(
            "TTS_PIPER_MODEL_ES", DEFAULT_TTS_PIPER_MODEL_ES
        ).strip(),
        piper_speaker_es=parse_int(
            "TTS_PIPER_SPEAKER_ES", DEFAULT_TTS_PIPER_SPEAKER_ES, min_value=0
        ),
        piper_model_quc=os.environ.get(
            "TTS_PIPER_MODEL_QUC", DEFAULT_TTS_PIPER_MODEL_QUC
        ).strip(),
        piper_speaker_quc=parse_int(
            "TTS_PIPER_SPEAKER_QUC", DEFAULT_TTS_PIPER_SPEAKER_QUC, min_value=0
        ),
        piper_length_scale=parse_float(
            "TTS_PIPER_LENGTH_SCALE",
            DEFAULT_TTS_PIPER_LENGTH_SCALE,
            min_value=0.5,
            max_value=2.5,
        ),
        piper_noise_scale=parse_float(
            "TTS_PIPER_NOISE_SCALE",
            DEFAULT_TTS_PIPER_NOISE_SCALE,
            min_value=0.0,
            max_value=2.0,
        ),
        piper_noise_w_scale=parse_float(
            "TTS_PIPER_NOISE_W_SCALE",
            DEFAULT_TTS_PIPER_NOISE_W_SCALE,
            min_value=0.0,
            max_value=2.0,
        ),
    )
