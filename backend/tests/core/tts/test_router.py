"""Unit tests for TTS routing, fallback, and in-memory LRU audio caching."""

from unittest.mock import MagicMock, patch

import pytest

from core.config import clear_settings_cache
from core.tts.exceptions import TTSUnavailableError
from core.tts.router import (
    TTSRouter,
    clear_speech_cache,
    get_tts_router,
    synthesize_speech,
)

FAKE_PIPER_WAV = b"RIFF-PIPER-WAV"
FAKE_ESPEAK_WAV = b"RIFF-ESPEAK-WAV"


@pytest.fixture(autouse=True)
def _clean_router_settings(monkeypatch: pytest.MonkeyPatch):
    """Hermetically isolates TTS configuration and clears the global speech cache."""
    for name in (
        "TTS_ENABLED",
        "TTS_ENGINE",
        "TTS_VOICE",
        "TTS_VOICE_QUC",
        "TTS_PIPER_MODEL_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    clear_settings_cache()
    clear_speech_cache()
    yield
    clear_settings_cache()
    clear_speech_cache()


def _make_mock_router():
    """Builds a router with controllable mocks for every auto-tier backend."""
    mock_piper = MagicMock()
    mock_piper.is_available.return_value = True
    mock_piper.synthesize.return_value = FAKE_PIPER_WAV

    mock_espeak = MagicMock()
    mock_espeak.is_available.return_value = True
    mock_espeak.synthesize.return_value = FAKE_ESPEAK_WAV

    mock_sherpa = MagicMock()
    mock_sherpa.engine_name = "sherpa"
    mock_sherpa.is_available.return_value = False

    mock_qwen = MagicMock()
    mock_qwen.engine_name = "qwen3-tts"
    mock_qwen.is_available.return_value = False

    router = TTSRouter(
        piper=mock_piper,
        espeak=mock_espeak,
        sherpa=mock_sherpa,
        qwen=mock_qwen,
    )
    return router, mock_piper, mock_espeak


def test_select_backend_auto_prefers_piper_when_available():
    """Verifies auto reaches Piper after Qwen3-TTS and Sherpa are unavailable."""
    router, mock_piper, _ = _make_mock_router()
    backend = router.select_backend("es")
    assert backend is mock_piper


def test_select_backend_auto_falls_back_to_espeak_when_piper_unavailable():
    """Verifies auto reaches eSpeak when neural Spanish tiers are absent."""
    router, mock_piper, mock_espeak = _make_mock_router()
    mock_piper.is_available.return_value = False
    backend = router.select_backend("es")
    assert backend is mock_espeak


def test_select_backend_auto_prefers_qwen3_tts():
    """Verifies Qwen3-TTS is the first automatic Spanish tier."""
    router, _, _ = _make_mock_router()
    mock_qwen = MagicMock()
    mock_qwen.engine_name = "qwen3-tts"
    mock_qwen.is_available.return_value = True
    router.qwen = mock_qwen
    router._backends["qwen3-tts"] = mock_qwen
    router._backends["qwen"] = mock_qwen

    assert router.select_backend("es") is mock_qwen


def test_select_backend_explicit_espeak(monkeypatch: pytest.MonkeyPatch):
    """Verifies TTS_ENGINE='espeak' forces eSpeak even if Piper is available."""
    monkeypatch.setenv("TTS_ENGINE", "espeak")
    clear_settings_cache()
    router, _, mock_espeak = _make_mock_router()
    assert router.select_backend("es") is mock_espeak


def test_select_backend_explicit_piper(monkeypatch: pytest.MonkeyPatch):
    """Verifies TTS_ENGINE='piper' raises if Piper model is missing."""
    monkeypatch.setenv("TTS_ENGINE", "piper")
    clear_settings_cache()
    router, mock_piper, _ = _make_mock_router()
    assert router.select_backend("es") is mock_piper

    mock_piper.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="Piper Spanish model"):
        router.select_backend("es")


def test_select_backend_quc_routing(monkeypatch: pytest.MonkeyPatch):
    """Verifies Mayan K'iche' routes strictly to Piper or configured eSpeak."""
    router, mock_piper, mock_espeak = _make_mock_router()

    # 1. Piper has K'iche' model
    mock_piper.is_available.side_effect = lambda v: v == "quc"
    assert router.select_backend("quc") is mock_piper

    # 2. Piper does not have K'iche', no eSpeak voice configured
    mock_piper.is_available.side_effect = None
    mock_piper.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="No speech voice is configured"):
        router.select_backend("quc")

    # 3. Piper absent, but TTS_VOICE_QUC configured on eSpeak
    monkeypatch.setenv("TTS_VOICE_QUC", "quc-voice")
    clear_settings_cache()
    assert router.select_backend("quc") is mock_espeak

    # 4. Explicit engine='espeak' without voice_quc
    monkeypatch.delenv("TTS_VOICE_QUC", raising=False)
    monkeypatch.setenv("TTS_ENGINE", "espeak")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="cannot synthesize Mayan"):
        router.select_backend("quc")

    # 5. Explicit engine='espeak' with voice_quc
    monkeypatch.setenv("TTS_VOICE_QUC", "quc-voice")
    clear_settings_cache()
    assert router.select_backend("quc") is mock_espeak


def test_synthesize_caches_and_evicts_lru(monkeypatch: pytest.MonkeyPatch):
    """Verifies synthesis results are cached and oldest entries are evicted."""
    router, mock_piper, _ = _make_mock_router()
    monkeypatch.setattr("core.tts.router._MAX_CACHE_ENTRIES", 2)

    # First call - cache miss
    audio1 = router.synthesize("Frase 1", lang="es")
    assert audio1 == FAKE_PIPER_WAV
    assert mock_piper.synthesize.call_count == 1

    # Second call same text - cache hit
    audio2 = router.synthesize("Frase 1", lang="es")
    assert audio2 == FAKE_PIPER_WAV
    assert mock_piper.synthesize.call_count == 1

    # Fill cache and cause eviction
    router.synthesize("Frase 2", lang="es")
    assert len(router._cache) == 2
    assert ("Frase 1", "es", "") in router._cache

    router.synthesize("Frase 3", lang="es")
    assert len(router._cache) == 2
    assert ("Frase 1", "es", "") not in router._cache
    assert ("Frase 3", "es", "") in router._cache


def test_get_backend_none_is_safe():
    """Verifies optional engine lookups do not call lower() on None."""
    router, _, _ = _make_mock_router()
    assert router.get_backend(None) is None


def test_synthesize_gracefully_falls_back_when_piper_crashes():
    """Verifies runtime Piper failure falls back to eSpeak for Spanish."""
    router, mock_piper, mock_espeak = _make_mock_router()
    mock_piper.synthesize.side_effect = TTSUnavailableError("Piper runtime crashed")

    audio = router.synthesize("Explicación de error", lang="es")
    assert audio == FAKE_ESPEAK_WAV
    mock_espeak.synthesize.assert_called_once()


def test_synthesize_quc_does_not_fallback_to_spanish_espeak():
    """Verifies Mayan synthesis does not silently fallback to Spanish eSpeak."""
    router, mock_piper, _ = _make_mock_router()
    mock_piper.synthesize.side_effect = TTSUnavailableError("Model missing")

    with pytest.raises(TTSUnavailableError, match="Model missing"):
        router.synthesize("Mayan text", lang="quc")


def test_synthesize_speech_and_clear_cache():
    """Verifies module-level convenience functions dispatch correctly."""
    router = get_tts_router()
    assert isinstance(router, TTSRouter)

    with patch.object(router, "synthesize", return_value=b"AUDIO"):
        audio = synthesize_speech("Test phrase", lang="es")
        assert audio == b"AUDIO"

    clear_speech_cache()
    assert len(router._cache) == 0


def test_synthesize_quc_via_espeak(monkeypatch: pytest.MonkeyPatch):
    """Verifies K'iche' speech synthesizes with configured voice_quc when routed to eSpeak."""
    router, mock_piper, mock_espeak = _make_mock_router()
    mock_piper.is_available.return_value = False
    mock_espeak.is_available.return_value = True
    monkeypatch.setenv("TTS_VOICE_QUC", "quc-voice")
    clear_settings_cache()

    audio = router.synthesize("Texto maya", lang="quc")
    assert audio == FAKE_ESPEAK_WAV
    mock_espeak.synthesize.assert_called_with("Texto maya", voice="quc-voice")


def test_select_backend_explicit_engine_no_fallback():
    """Verifies that an explicitly requested engine never falls back."""
    router, mock_piper, mock_espeak = _make_mock_router()

    assert router.select_backend("es", engine="piper") is mock_piper
    assert router.select_backend("es", engine="espeak") is mock_espeak

    mock_piper.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="unavailable for 'es'"):
        router.select_backend("es", engine="piper")

    with pytest.raises(TTSUnavailableError, match="not registered or not installed"):
        router.select_backend("es", engine="unknown_engine")

    mock_sherpa = MagicMock()
    mock_sherpa.engine_name = "sherpa"
    mock_sherpa.is_available.return_value = True
    mock_sherpa.is_loaded.return_value = True
    r_sherpa = TTSRouter(sherpa=mock_sherpa)
    assert r_sherpa.get_backend("sherpa") is mock_sherpa
    assert r_sherpa.status(engine="sherpa")["engine"] == "sherpa"

    mock_qwen = MagicMock()
    mock_qwen.engine_name = "qwen3-tts"
    mock_qwen.is_available.return_value = True
    mock_qwen.is_loaded.return_value = True
    r_qwen = TTSRouter(qwen=mock_qwen)
    assert r_qwen.get_backend("qwen3-tts") is mock_qwen
    assert r_qwen.get_backend("qwen") is mock_qwen
    assert r_qwen.status(engine="qwen")["engine"] == "qwen3-tts"
    assert r_qwen.unload("qwen3-tts") == "qwen3-tts"
    assert r_qwen.unload(None) == "all"


def test_select_backend_configured_engine_no_fallback(monkeypatch: pytest.MonkeyPatch):
    """Verifies configured TTS_ENGINE never falls back if not auto."""
    router, mock_piper, mock_espeak = _make_mock_router()

    monkeypatch.setenv("TTS_ENGINE", "moss-nano")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="not registered or not installed"):
        router.select_backend("es")

    monkeypatch.setenv("TTS_ENGINE", "espeak")
    clear_settings_cache()
    mock_espeak.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="unavailable for 'es'"):
        router.select_backend("es")

    monkeypatch.setenv("TTS_ENGINE", "auto")
    clear_settings_cache()
    mock_piper.is_available.return_value = False
    mock_espeak.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="No TTS engine available"):
        router.select_backend("es")


def test_select_backend_quc_additional_branches(monkeypatch: pytest.MonkeyPatch):
    """Verifies remaining K'iche' selection branches."""
    router, mock_piper, _ = _make_mock_router()

    monkeypatch.setenv("TTS_ENGINE", "piper")
    clear_settings_cache()
    mock_piper.is_available.side_effect = lambda v: v == "quc"
    assert router.select_backend("quc") is mock_piper

    mock_piper.is_available.side_effect = None
    mock_piper.is_available.return_value = False
    with pytest.raises(
        TTSUnavailableError, match="Piper K'iche' model is not installed"
    ):
        router.select_backend("quc")

    with pytest.raises(TTSUnavailableError, match="not registered or does not support"):
        router.select_backend("quc", engine="unknown_engine")


def test_synthesize_custom_voice_override():
    """Verifies explicit voice parameter overrides default voice mapping."""
    router, mock_piper, _ = _make_mock_router()
    router.synthesize("Texto", lang="es", voice="custom-voice-id")
    mock_piper.synthesize.assert_called_with("Texto", voice="custom-voice-id")
