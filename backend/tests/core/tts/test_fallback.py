"""Coverage for the multi-tier Spanish synthesis fallback ladder."""

from unittest.mock import MagicMock

import pytest

from core.config import clear_settings_cache
from core.tts.exceptions import TTSUnavailableError
from core.tts.router.fallback import synthesize_with_fallback


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch):
    monkeypatch.setenv("TTS_ENGINE", "auto")
    clear_settings_cache()
    yield
    clear_settings_cache()


def _backend(name: str) -> MagicMock:
    backend = MagicMock()
    backend.engine_name = name
    backend.is_available.return_value = True
    return backend


def test_fallback_skips_failed_neural_tier_then_succeeds():
    target = _backend("qwen3-tts")
    sherpa = _backend("sherpa")
    piper = _backend("piper")
    espeak = _backend("espeak")
    target.synthesize.side_effect = TTSUnavailableError("qwen unavailable")
    sherpa.synthesize.side_effect = TTSUnavailableError("sherpa unavailable")
    piper.synthesize.return_value = b"PIPER"

    audio = synthesize_with_fallback(
        {"qwen3-tts": target, "sherpa": sherpa, "piper": piper, "espeak": espeak},
        target,
        "Hola",
        "es",
        None,
        espeak,
        explicit_backend=False,
    )

    assert audio == b"PIPER"
    assert espeak.synthesize.call_count == 0


def test_fallback_raises_last_error_when_every_tier_fails():
    target = _backend("qwen3-tts")
    sherpa = _backend("sherpa")
    piper = _backend("piper")
    espeak = _backend("espeak")
    target.synthesize.side_effect = TTSUnavailableError("qwen unavailable")
    sherpa.synthesize.side_effect = TTSUnavailableError("sherpa unavailable")
    piper.synthesize.side_effect = TTSUnavailableError("piper unavailable")
    espeak.synthesize.side_effect = TTSUnavailableError("espeak unavailable")

    with pytest.raises(TTSUnavailableError, match="espeak unavailable"):
        synthesize_with_fallback(
            {"qwen3-tts": target, "sherpa": sherpa, "piper": piper, "espeak": espeak},
            target,
            "Hola",
            "es",
            None,
            espeak,
            explicit_backend=False,
        )
