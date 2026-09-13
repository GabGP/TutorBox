"""Tests for the TTS configuration builder (src/core/config/tts_settings.py)."""

from core.config import (
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
    clear_settings_cache,
    get_settings,
)
from core.config.tts_settings import build_tts_config


def test_build_tts_config_defaults() -> None:
    """Verifies default values when no environment variables are set."""
    config = build_tts_config()
    assert config.enabled == DEFAULT_TTS_ENABLED
    assert config.binary == DEFAULT_TTS_BINARY
    assert config.voice == DEFAULT_TTS_VOICE
    assert config.voice_quc == DEFAULT_TTS_VOICE_QUC
    assert config.words_per_minute == DEFAULT_TTS_WORDS_PER_MINUTE
    assert config.pitch == DEFAULT_TTS_PITCH
    assert config.amplitude == DEFAULT_TTS_AMPLITUDE
    assert config.timeout_seconds == DEFAULT_TTS_TIMEOUT_SECONDS
    assert config.max_chars == DEFAULT_TTS_MAX_CHARS


def test_build_tts_config_env_overrides(monkeypatch) -> None:
    """Verifies espeak voice settings are configurable via environment."""
    monkeypatch.setenv("TTS_ENABLED", "false")
    monkeypatch.setenv("TTS_ESPEAK_BINARY", " /opt/espeak-ng ")
    monkeypatch.setenv("TTS_VOICE", "es-la")
    monkeypatch.setenv("TTS_VOICE_QUC", "quc")
    monkeypatch.setenv("TTS_WORDS_PER_MINUTE", "130")
    monkeypatch.setenv("TTS_PITCH", "60")
    monkeypatch.setenv("TTS_AMPLITUDE", "150")
    monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "15.5")
    monkeypatch.setenv("TTS_MAX_CHARS", "800")

    config = build_tts_config()
    assert config.enabled is False
    assert config.binary == "/opt/espeak-ng"
    assert config.voice == "es-la"
    assert config.voice_quc == "quc"
    assert config.words_per_minute == 130
    assert config.pitch == 60
    assert config.amplitude == 150
    assert config.timeout_seconds == 15.5
    assert config.max_chars == 800


def test_build_tts_config_bounds_and_fallbacks(monkeypatch) -> None:
    """Verifies out-of-range cadence and parameters fall back to defaults."""
    monkeypatch.setenv("TTS_WORDS_PER_MINUTE", "900")
    monkeypatch.setenv("TTS_PITCH", "200")
    monkeypatch.setenv("TTS_AMPLITUDE", "500")
    monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setenv("TTS_MAX_CHARS", "10")

    config = build_tts_config()
    assert config.words_per_minute == DEFAULT_TTS_WORDS_PER_MINUTE
    assert config.pitch == DEFAULT_TTS_PITCH
    assert config.amplitude == DEFAULT_TTS_AMPLITUDE
    assert config.timeout_seconds == DEFAULT_TTS_TIMEOUT_SECONDS
    assert config.max_chars == DEFAULT_TTS_MAX_CHARS


def test_get_settings_integrates_tts_config(monkeypatch) -> None:
    """Verifies get_settings correctly integrates build_tts_config."""
    monkeypatch.setenv("TTS_VOICE", "es-test")
    clear_settings_cache()
    try:
        settings = get_settings()
        assert settings.tts.voice == "es-test"
    finally:
        clear_settings_cache()
