import os

from core.config.constants import (
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_KOKORO_MODEL_DIR,
    DEFAULT_TTS_KOKORO_MODEL_FILE,
    DEFAULT_TTS_KOKORO_PROVIDER,
    DEFAULT_TTS_KOKORO_SPEAKER_ID,
    DEFAULT_TTS_KOKORO_VOICE,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_MELO_VOICE,
    DEFAULT_TTS_MOSS_MODEL,
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
    DEFAULT_TTS_QWEN_BINARY,
    DEFAULT_TTS_QWEN_GGUF_PATH,
    DEFAULT_TTS_QWEN_THREADS,
    DEFAULT_TTS_SHERPA_MODEL_ES,
    DEFAULT_TTS_SHERPA_PROVIDER,
    DEFAULT_TTS_SHERPA_THREADS,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)
from core.config.models import TTSConfig
from core.config.parsers import parse_bool, parse_float, parse_int

__all__ = ["build_tts_config"]

_VALID_ENGINES: frozenset[str] = frozenset(
    {
        "auto",
        "piper",
        "espeak",
        "sherpa",
        "moss-nano",
        "kokoro",
        "melo",
        "qwen-gguf",
        "qwen3-tts",
        "qwen",
    }
)
_VALID_PROVIDERS: frozenset[str] = frozenset({"auto", "cpu", "cuda"})


def build_tts_config() -> TTSConfig:
    """Reads TTS_* environment variables and returns a typed TTSConfig instance."""
    _env = os.environ.get
    engine = _env("TTS_ENGINE", "").strip().lower()
    provider = _env("TTS_SHERPA_PROVIDER", "").strip().lower()
    kokoro_provider = _env("TTS_KOKORO_PROVIDER", "").strip().lower()
    return TTSConfig(
        enabled=parse_bool("TTS_ENABLED", DEFAULT_TTS_ENABLED),
        engine=engine if engine in _VALID_ENGINES else DEFAULT_TTS_ENGINE,
        binary=_env("TTS_ESPEAK_BINARY", DEFAULT_TTS_BINARY).strip(),
        voice=_env("TTS_VOICE") or DEFAULT_TTS_VOICE,
        voice_quc=_env("TTS_VOICE_QUC", DEFAULT_TTS_VOICE_QUC).strip(),
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
        piper_binary=_env("TTS_PIPER_BINARY", DEFAULT_TTS_PIPER_BINARY).strip(),
        piper_model_dir=_env(
            "TTS_PIPER_MODEL_DIR", DEFAULT_TTS_PIPER_MODEL_DIR
        ).strip(),
        piper_model_es=_env("TTS_PIPER_MODEL_ES", DEFAULT_TTS_PIPER_MODEL_ES).strip(),
        piper_speaker_es=parse_int(
            "TTS_PIPER_SPEAKER_ES", DEFAULT_TTS_PIPER_SPEAKER_ES, min_value=0
        ),
        piper_model_quc=_env(
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
        sherpa_model_es=_env(
            "TTS_SHERPA_MODEL_ES", DEFAULT_TTS_SHERPA_MODEL_ES
        ).strip(),
        sherpa_threads=parse_int(
            "TTS_SHERPA_THREADS", DEFAULT_TTS_SHERPA_THREADS, min_value=1, max_value=16
        ),
        sherpa_provider=(
            provider if provider in _VALID_PROVIDERS else DEFAULT_TTS_SHERPA_PROVIDER
        ),
        moss_model=_env("TTS_MOSS_MODEL", DEFAULT_TTS_MOSS_MODEL).strip(),
        kokoro_voice=_env("TTS_KOKORO_VOICE", DEFAULT_TTS_KOKORO_VOICE).strip(),
        kokoro_model_dir=_env(
            "TTS_KOKORO_MODEL_DIR", DEFAULT_TTS_KOKORO_MODEL_DIR
        ).strip(),
        kokoro_model_file=_env(
            "TTS_KOKORO_MODEL_FILE", DEFAULT_TTS_KOKORO_MODEL_FILE
        ).strip(),
        kokoro_speaker_id=parse_int(
            "TTS_KOKORO_SPEAKER_ID", DEFAULT_TTS_KOKORO_SPEAKER_ID, min_value=0
        ),
        kokoro_provider=(
            kokoro_provider
            if kokoro_provider in _VALID_PROVIDERS
            else DEFAULT_TTS_KOKORO_PROVIDER
        ),
        melo_voice=_env("TTS_MELO_VOICE", DEFAULT_TTS_MELO_VOICE).strip(),
        qwen_binary=_env("TTS_QWEN_BINARY", DEFAULT_TTS_QWEN_BINARY).strip(),
        qwen_gguf_path=_env("TTS_QWEN_GGUF_PATH", DEFAULT_TTS_QWEN_GGUF_PATH).strip(),
        qwen_threads=parse_int(
            "TTS_QWEN_THREADS", DEFAULT_TTS_QWEN_THREADS, min_value=1, max_value=16
        ),
    )
