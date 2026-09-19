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


def test_fallback_ultimate_espeak_safety_net_succeeds():
    """Verifies ultimate safety net synthesizes when espeak is omitted from backends dict."""
    target = _backend("piper")
    espeak = _backend("espeak")
    target.synthesize.side_effect = RuntimeError("Piper crashed")
    espeak.synthesize.return_value = b"ESPEAK_FALLBACK"

    audio = synthesize_with_fallback(
        {"piper": target},
        target,
        "Hola",
        "es",
        None,
        espeak,
        explicit_backend=False,
    )
    assert audio == b"ESPEAK_FALLBACK"


def test_fallback_ultimate_espeak_safety_net_fails():
    """Verifies ultimate safety net raises last error when espeak also fails."""
    target = _backend("piper")
    espeak = _backend("espeak")
    target.synthesize.side_effect = RuntimeError("Piper crashed")
    espeak.synthesize.side_effect = RuntimeError("eSpeak also crashed")

    with pytest.raises(RuntimeError, match="eSpeak also crashed"):
        synthesize_with_fallback(
            {"piper": target},
            target,
            "Hola",
            "es",
            None,
            espeak,
            explicit_backend=False,
        )


def test_preload_with_fallback_success():
    """Verifies preload_with_fallback tries candidates in order."""
    from core.tts.router.fallback import preload_with_fallback

    qwen = _backend("qwen3-tts")
    qwen.preload.side_effect = RuntimeError("Qwen failed")
    piper = _backend("piper")
    piper.preload.return_value = 8.5

    engine, load_ms = preload_with_fallback({"qwen3-tts": qwen, "piper": piper})
    assert engine == "piper"
    assert load_ms == 8.5


def test_preload_with_fallback_no_backends():
    """Verifies preload_with_fallback raises error when candidate list is empty."""
    from core.tts.router.fallback import preload_with_fallback

    with pytest.raises(TTSUnavailableError, match="No TTS engine available"):
        preload_with_fallback({})

