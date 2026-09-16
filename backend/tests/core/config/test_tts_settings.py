"""Tests for the TTS configuration builder (src/core/config/tts_settings.py)."""

import pytest

from core.config import (
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
    DEFAULT_TTS_QWEN_GGUF_PATH,
    DEFAULT_TTS_QWEN_THREADS,
    DEFAULT_TTS_SHERPA_MODEL_ES,
    DEFAULT_TTS_SHERPA_PROVIDER,
    DEFAULT_TTS_SHERPA_THREADS,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
    clear_settings_cache,
    get_settings,
)
from core.config.tts_settings import build_tts_config

_TTS_ENV_VARS = (
    "TTS_ENABLED",
    "TTS_ENGINE",
    "TTS_ESPEAK_BINARY",
    "TTS_VOICE",
    "TTS_VOICE_QUC",
    "TTS_WORDS_PER_MINUTE",
    "TTS_PITCH",
    "TTS_AMPLITUDE",
    "TTS_TIMEOUT_SECONDS",
    "TTS_MAX_CHARS",
    "TTS_PIPER_BINARY",
    "TTS_PIPER_MODEL_DIR",
    "TTS_PIPER_MODEL_ES",
    "TTS_PIPER_MODEL_QUC",
    "TTS_PIPER_SPEAKER_ES",
    "TTS_PIPER_SPEAKER_QUC",
    "TTS_PIPER_LENGTH_SCALE",
    "TTS_PIPER_NOISE_SCALE",
    "TTS_PIPER_NOISE_W_SCALE",
    "TTS_SHERPA_MODEL_ES",
    "TTS_SHERPA_PROVIDER",
    "TTS_SHERPA_THREADS",
    "TTS_MOSS_MODEL",
    "TTS_KOKORO_VOICE",
    "TTS_KOKORO_MODEL_DIR",
    "TTS_KOKORO_MODEL_FILE",
    "TTS_KOKORO_SPEAKER_ID",
    "TTS_KOKORO_PROVIDER",
    "TTS_MELO_VOICE",
    "TTS_QWEN_GGUF_PATH",
    "TTS_QWEN_THREADS",
)


@pytest.fixture(autouse=True)
def _clean_tts_env(monkeypatch: pytest.MonkeyPatch):
    """Keeps TTS environment hermetic across test execution."""
    for var in _TTS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_build_tts_config_defaults() -> None:
    """Verifies default values when no environment variables are set."""
    config = build_tts_config()
    assert config.enabled == DEFAULT_TTS_ENABLED
    assert config.engine == DEFAULT_TTS_ENGINE
    assert config.binary == DEFAULT_TTS_BINARY
    assert config.voice == DEFAULT_TTS_VOICE
    assert config.voice_quc == DEFAULT_TTS_VOICE_QUC
    assert config.words_per_minute == DEFAULT_TTS_WORDS_PER_MINUTE
    assert config.pitch == DEFAULT_TTS_PITCH
    assert config.amplitude == DEFAULT_TTS_AMPLITUDE
    assert config.timeout_seconds == DEFAULT_TTS_TIMEOUT_SECONDS
    assert config.max_chars == DEFAULT_TTS_MAX_CHARS

    # Neural Piper defaults
    assert config.piper_binary == DEFAULT_TTS_PIPER_BINARY
    assert config.piper_model_dir == DEFAULT_TTS_PIPER_MODEL_DIR
    assert config.piper_model_es == DEFAULT_TTS_PIPER_MODEL_ES
    assert config.piper_speaker_es == DEFAULT_TTS_PIPER_SPEAKER_ES
    assert config.piper_model_quc == DEFAULT_TTS_PIPER_MODEL_QUC
    assert config.piper_speaker_quc == DEFAULT_TTS_PIPER_SPEAKER_QUC
    assert config.piper_length_scale == DEFAULT_TTS_PIPER_LENGTH_SCALE
    assert config.piper_noise_scale == DEFAULT_TTS_PIPER_NOISE_SCALE
    assert config.piper_noise_w_scale == DEFAULT_TTS_PIPER_NOISE_W_SCALE

    # Candidate engine defaults
    assert config.sherpa_model_es == DEFAULT_TTS_SHERPA_MODEL_ES
    assert config.sherpa_threads == DEFAULT_TTS_SHERPA_THREADS
    assert config.sherpa_provider == DEFAULT_TTS_SHERPA_PROVIDER
    assert config.moss_model == DEFAULT_TTS_MOSS_MODEL
    assert config.kokoro_voice == DEFAULT_TTS_KOKORO_VOICE
    assert config.kokoro_model_dir == DEFAULT_TTS_KOKORO_MODEL_DIR
    assert config.kokoro_model_file == DEFAULT_TTS_KOKORO_MODEL_FILE
    assert config.kokoro_speaker_id == DEFAULT_TTS_KOKORO_SPEAKER_ID
    assert config.kokoro_provider == DEFAULT_TTS_KOKORO_PROVIDER
    assert config.melo_voice == DEFAULT_TTS_MELO_VOICE
    assert config.qwen_gguf_path == DEFAULT_TTS_QWEN_GGUF_PATH
    assert config.qwen_threads == DEFAULT_TTS_QWEN_THREADS


def test_build_tts_config_env_overrides(monkeypatch) -> None:
    """Verifies all TTS settings are configurable via environment variables."""
    monkeypatch.setenv("TTS_ENABLED", "false")
    monkeypatch.setenv("TTS_ENGINE", "piper")
    monkeypatch.setenv("TTS_ESPEAK_BINARY", " /opt/espeak-ng ")
    monkeypatch.setenv("TTS_VOICE", "es-la")
    monkeypatch.setenv("TTS_VOICE_QUC", "quc")
    monkeypatch.setenv("TTS_WORDS_PER_MINUTE", "130")
    monkeypatch.setenv("TTS_PITCH", "60")
    monkeypatch.setenv("TTS_AMPLITUDE", "150")
    monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "15.5")
    monkeypatch.setenv("TTS_MAX_CHARS", "800")

    monkeypatch.setenv("TTS_PIPER_BINARY", " /usr/local/bin/piper ")
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", " /var/models/tts ")
    monkeypatch.setenv("TTS_PIPER_MODEL_ES", "custom_es.onnx")
    monkeypatch.setenv("TTS_PIPER_SPEAKER_ES", "2")
    monkeypatch.setenv("TTS_PIPER_MODEL_QUC", "custom_quc.onnx")
    monkeypatch.setenv("TTS_PIPER_SPEAKER_QUC", "3")
    monkeypatch.setenv("TTS_PIPER_LENGTH_SCALE", "1.25")
    monkeypatch.setenv("TTS_PIPER_NOISE_SCALE", "0.45")
    monkeypatch.setenv("TTS_PIPER_NOISE_W_SCALE", "0.55")

    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "custom_sherpa.onnx")
    monkeypatch.setenv("TTS_SHERPA_THREADS", "8")
    monkeypatch.setenv("TTS_SHERPA_PROVIDER", "cuda")
    monkeypatch.setenv("TTS_MOSS_MODEL", "custom_moss.onnx")
    monkeypatch.setenv("TTS_KOKORO_VOICE", "custom_kokoro")
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", "custom_kokoro_dir")
    monkeypatch.setenv("TTS_KOKORO_MODEL_FILE", "custom_kokoro.onnx")
    monkeypatch.setenv("TTS_KOKORO_SPEAKER_ID", "42")
    monkeypatch.setenv("TTS_KOKORO_PROVIDER", "cuda")
    monkeypatch.setenv("TTS_MELO_VOICE", "custom_melo")
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", "/path/to/qwen.gguf")
    monkeypatch.setenv("TTS_QWEN_THREADS", "6")

    config = build_tts_config()
    assert config.enabled is False
    assert config.engine == "piper"
    assert config.binary == "/opt/espeak-ng"
    assert config.voice == "es-la"
    assert config.voice_quc == "quc"
    assert config.words_per_minute == 130
    assert config.pitch == 60
    assert config.amplitude == 150
    assert config.timeout_seconds == 15.5
    assert config.max_chars == 800

    assert config.piper_binary == "/usr/local/bin/piper"
    assert config.piper_model_dir == "/var/models/tts"
    assert config.piper_model_es == "custom_es.onnx"
    assert config.piper_speaker_es == 2
    assert config.piper_model_quc == "custom_quc.onnx"
    assert config.piper_speaker_quc == 3
    assert config.piper_length_scale == 1.25
    assert config.piper_noise_scale == 0.45
    assert config.piper_noise_w_scale == 0.55

    assert config.sherpa_model_es == "custom_sherpa.onnx"
    assert config.sherpa_threads == 8
    assert config.sherpa_provider == "cuda"
    assert config.moss_model == "custom_moss.onnx"
    assert config.kokoro_voice == "custom_kokoro"
    assert config.kokoro_model_dir == "custom_kokoro_dir"
    assert config.kokoro_model_file == "custom_kokoro.onnx"
    assert config.kokoro_speaker_id == 42
    assert config.kokoro_provider == "cuda"
    assert config.melo_voice == "custom_melo"
    assert config.qwen_gguf_path == "/path/to/qwen.gguf"
    assert config.qwen_threads == 6


def test_build_tts_config_bounds_and_fallbacks(monkeypatch) -> None:
    """Verifies out-of-range parameters fall back to safe defaults."""
    monkeypatch.setenv("TTS_WORDS_PER_MINUTE", "900")
    monkeypatch.setenv("TTS_PITCH", "200")
    monkeypatch.setenv("TTS_AMPLITUDE", "500")
    monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setenv("TTS_MAX_CHARS", "10")

    monkeypatch.setenv("TTS_ENGINE", "unknown_engine")
    monkeypatch.setenv("TTS_SHERPA_PROVIDER", "invalid_provider")
    monkeypatch.setenv("TTS_KOKORO_PROVIDER", "invalid_provider")
    monkeypatch.setenv("TTS_KOKORO_SPEAKER_ID", "-1")
    monkeypatch.setenv("TTS_PIPER_SPEAKER_ES", "-1")
    monkeypatch.setenv("TTS_PIPER_LENGTH_SCALE", "5.0")
    monkeypatch.setenv("TTS_PIPER_NOISE_SCALE", "-0.5")
    monkeypatch.setenv("TTS_PIPER_NOISE_W_SCALE", "9.0")

    config = build_tts_config()
    assert config.words_per_minute == DEFAULT_TTS_WORDS_PER_MINUTE
    assert config.pitch == DEFAULT_TTS_PITCH
    assert config.amplitude == DEFAULT_TTS_AMPLITUDE
    assert config.timeout_seconds == DEFAULT_TTS_TIMEOUT_SECONDS
    assert config.max_chars == DEFAULT_TTS_MAX_CHARS

    assert config.engine == DEFAULT_TTS_ENGINE
    assert config.sherpa_provider == DEFAULT_TTS_SHERPA_PROVIDER
    assert config.kokoro_provider == DEFAULT_TTS_KOKORO_PROVIDER
    assert config.kokoro_speaker_id == DEFAULT_TTS_KOKORO_SPEAKER_ID
    assert config.piper_speaker_es == DEFAULT_TTS_PIPER_SPEAKER_ES
    assert config.piper_length_scale == DEFAULT_TTS_PIPER_LENGTH_SCALE
    assert config.piper_noise_scale == DEFAULT_TTS_PIPER_NOISE_SCALE
    assert config.piper_noise_w_scale == DEFAULT_TTS_PIPER_NOISE_W_SCALE


def test_build_tts_config_engine_variants(monkeypatch) -> None:
    """Verifies valid engine case normalization and candidate variants."""
    for eng in (
        "espeak",
        "piper",
        "auto",
        "sherpa",
        "moss-nano",
        "kokoro",
        "melo",
        "qwen-gguf",
    ):
        monkeypatch.setenv("TTS_ENGINE", f" {eng.upper()} ")
        assert build_tts_config().engine == eng


def test_get_settings_integrates_tts_config(monkeypatch) -> None:
    """Verifies get_settings correctly integrates build_tts_config."""
    monkeypatch.setenv("TTS_VOICE", "es-test")
    monkeypatch.setenv("TTS_ENGINE", "piper")
    clear_settings_cache()
    try:
        settings = get_settings()
        assert settings.tts.voice == "es-test"
        assert settings.tts.engine == "piper"
    finally:
        clear_settings_cache()
