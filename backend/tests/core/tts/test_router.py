"""Unit tests for the pluggable TTS router and in-memory LRU audio caching.

Tests engine selection, Spanish/K'iche' dispatch, neural-to-formant fallback,
and cache hit/eviction semantics.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.config import clear_settings_cache
from core.tts.espeak import TTSUnavailableError
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
    """Builds a TTSRouter with controllable mock Piper and eSpeak backends."""
    mock_piper = MagicMock()
    mock_piper.is_available.return_value = True
    mock_piper.synthesize.return_value = FAKE_PIPER_WAV

    mock_espeak = MagicMock()
    mock_espeak.is_available.return_value = True
    mock_espeak.synthesize.return_value = FAKE_ESPEAK_WAV

    router = TTSRouter(piper=mock_piper, espeak=mock_espeak)
    return router, mock_piper, mock_espeak


def test_select_backend_auto_prefers_piper_when_available():
    """Verifies default 'auto' engine prefers Piper when its model is present."""
    router, mock_piper, _ = _make_mock_router()
    backend = router.select_backend("es")
    assert backend is mock_piper


def test_select_backend_auto_falls_back_to_espeak_when_piper_unavailable():
    """Verifies default 'auto' engine falls back to eSpeak when Piper is absent."""
    router, mock_piper, mock_espeak = _make_mock_router()
    mock_piper.is_available.return_value = False
    backend = router.select_backend("es")
    assert backend is mock_espeak


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
