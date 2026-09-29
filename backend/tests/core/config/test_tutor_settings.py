"""TUTOR_* settings for the Socratic tutor (core/config/tutor_settings.py)."""

import pytest

from core.config.tutor_settings import (
    DEFAULT_TUTOR_MODEL_NAME,
    TutorConfig,
    load_tutor_config,
)

_NAMES = (
    "TUTOR_MODEL_NAME",
    "TUTOR_TEMPERATURE",
    "TUTOR_MAX_TOKENS",
    "TUTOR_TIMEOUT_SECONDS",
    "TUTOR_MAX_CONCURRENT",
    "TUTOR_QUEUE_SECONDS",
    "TUTOR_TURNS_PER_MINUTE",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in _NAMES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_use_the_deepseek_distill_on_ollama():
    assert load_tutor_config() == TutorConfig()
    assert TutorConfig().model_name == DEFAULT_TUTOR_MODEL_NAME
    assert "DeepSeek-R1-Distill-Qwen-1.5B" in DEFAULT_TUTOR_MODEL_NAME


def test_env_overrides_and_invalid_values_fall_back(monkeypatch):
    monkeypatch.setenv("TUTOR_MODEL_NAME", "  otro:1b  ")
    monkeypatch.setenv("TUTOR_TEMPERATURE", "0.3")
    monkeypatch.setenv("TUTOR_MAX_TOKENS", "5")  # below the floor
    monkeypatch.setenv("TUTOR_TIMEOUT_SECONDS", "abc")
    monkeypatch.setenv("TUTOR_MAX_CONCURRENT", "3")
    monkeypatch.setenv("TUTOR_QUEUE_SECONDS", "0")
    monkeypatch.setenv("TUTOR_TURNS_PER_MINUTE", "30")

    assert load_tutor_config() == TutorConfig(
        model_name="otro:1b",
        temperature=0.3,
        max_concurrent=3,
        queue_seconds=0.0,
        turns_per_minute=30,
    )


def test_blank_model_name_keeps_the_default(monkeypatch):
    monkeypatch.setenv("TUTOR_MODEL_NAME", "   ")

    assert load_tutor_config().model_name == DEFAULT_TUTOR_MODEL_NAME
