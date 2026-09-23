"""Unit tests for TTS engine lifecycle (preload, unload, status, readiness)."""

from unittest.mock import MagicMock, patch

import pytest

from core.tts.engines.espeak import EspeakBackend
from core.tts.engines.piper import PiperBackend
from core.tts.exceptions import TTSUnavailableError
from core.tts.router import TTSRouter


def test_espeak_lifecycle_protocol() -> None:
    """Verifies EspeakBackend implements the lifecycle protocol."""
    backend = EspeakBackend()
    assert backend.engine_name == "espeak"

    with patch.object(backend, "is_available", return_value=True):
        assert backend.is_loaded() is True
        load_ms = backend.preload("es-419")
        assert load_ms >= 0.0
        assert backend.unload() is None

    with patch.object(backend, "is_available", return_value=False):
        assert backend.is_loaded() is False
        with pytest.raises(TTSUnavailableError):
            backend.preload("invalid_voice")


def test_piper_lifecycle_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies PiperBackend implements preload, unload, and is_loaded."""
    backend = PiperBackend()
    assert backend.engine_name == "piper"

    # Preload when disabled raises TTSUnavailableError
    monkeypatch.setenv("TTS_ENABLED", "false")
    from core.config import clear_settings_cache

    clear_settings_cache()
    with pytest.raises(TTSUnavailableError):
        backend.preload("es")

    monkeypatch.setenv("TTS_ENABLED", "true")
    clear_settings_cache()

    # Preload mock success
    with (
        patch(
            "core.tts.engines.piper.engine.resolve_model_path", return_value=MagicMock()
        ),
        patch("core.tts.engines.piper.engine.sanitize_model_config"),
        patch("piper.voice.PiperVoice.load", return_value=MagicMock()),
    ):
        load_ms = backend.preload("es")
        assert load_ms >= 0.0
        assert backend.is_loaded() is True

        backend.unload()
        assert backend.is_loaded() is False


def test_router_lifecycle_methods() -> None:
    """Verifies TTSRouter preload, unload, and status dispatch."""
    mock_piper = MagicMock()
    mock_piper.engine_name = "piper"
    mock_piper.is_available.return_value = True
    mock_piper.is_loaded.return_value = False
    mock_piper.preload.return_value = 12.5

    mock_espeak = MagicMock()
    mock_espeak.engine_name = "espeak"
    mock_espeak.is_available.return_value = True
    mock_espeak.is_loaded.return_value = True
    mock_espeak.preload.return_value = 0.5

    router = TTSRouter(piper=mock_piper, espeak=mock_espeak)
    assert router.get_backend("piper") is mock_piper
    assert router.get_backend("espeak") is mock_espeak
    assert router.get_backend("unknown") is None

    # Preload defaults to active engine (piper in auto)
    engine, load_ms = router.preload(engine="piper")
    assert engine == "piper"
    assert load_ms == 12.5
    mock_piper.preload.assert_called_once()

    # Status check
    status = router.status(engine="piper")
    assert status["engine"] == "piper"
    assert status["loaded"] is False

    # Unload specific engine
    router._cache[("test", "es", "")] = b"audio"
    unloaded = router.unload("piper")
    assert unloaded == "piper"
    assert len(router._cache) == 0
    mock_piper.unload.assert_called_once()

    # Unload all engines
    unloaded_all = router.unload()
    assert unloaded_all == "all"
    mock_espeak.unload.assert_called_once()


def test_router_select_backend_with_explicit_engine_override() -> None:
    """Verifies router obeys explicit engine parameter."""
    mock_piper = MagicMock()
    mock_piper.is_available.return_value = True
    mock_espeak = MagicMock()
    mock_espeak.is_available.return_value = True

    router = TTSRouter(piper=mock_piper, espeak=mock_espeak)
    assert router.select_backend(lang="es", engine="espeak") is mock_espeak
    assert router.select_backend(lang="es", engine="piper") is mock_piper

    # Unavailable engine override raises
    mock_piper.is_available.return_value = False
    with pytest.raises(TTSUnavailableError, match="Engine 'piper' is unavailable"):
        router.select_backend(lang="es", engine="piper")


def test_router_preload_auto_fallback() -> None:
    """Verifies router.preload falls back across auto-tier engines when primary fails."""
    mock_sherpa = MagicMock()
    mock_sherpa.engine_name = "sherpa"
    mock_sherpa.is_available.return_value = True
    mock_sherpa.preload.side_effect = RuntimeError("Sherpa preload failed")

    mock_piper = MagicMock()
    mock_piper.engine_name = "piper"
    mock_piper.is_available.return_value = True
    mock_piper.preload.return_value = 14.2

    mock_espeak = MagicMock()
    mock_espeak.engine_name = "espeak"
    mock_espeak.is_available.return_value = True
    mock_espeak.preload.return_value = 0.5

    mock_qwen = MagicMock()
    mock_qwen.engine_name = "qwen3-tts"
    mock_qwen.is_available.return_value = False

    router = TTSRouter(
        piper=mock_piper,
        espeak=mock_espeak,
        sherpa=mock_sherpa,
        qwen=mock_qwen,
    )
    engine, load_ms = router.preload(engine="auto")
    assert engine == "piper"
    assert load_ms == 14.2
    mock_sherpa.preload.assert_called_once()
    mock_piper.preload.assert_called_once()


def test_router_preload_auto_all_engines_fail() -> None:
    """Verifies router.preload raises TTSUnavailableError when all auto engines fail."""
    mock_piper = MagicMock()
    mock_piper.engine_name = "piper"
    mock_piper.is_available.return_value = True
    mock_piper.preload.side_effect = RuntimeError("Piper failed")

    mock_espeak = MagicMock()
    mock_espeak.engine_name = "espeak"
    mock_espeak.is_available.return_value = True
    mock_espeak.preload.side_effect = RuntimeError("eSpeak failed")

    mock_sherpa = MagicMock()
    mock_sherpa.engine_name = "sherpa"
    mock_sherpa.is_available.return_value = True
    mock_sherpa.preload.side_effect = RuntimeError("Sherpa failed")

    mock_qwen = MagicMock()
    mock_qwen.engine_name = "qwen3-tts"
    mock_qwen.is_available.return_value = False

    router = TTSRouter(
        piper=mock_piper,
        espeak=mock_espeak,
        sherpa=mock_sherpa,
        qwen=mock_qwen,
    )
    with pytest.raises(
        TTSUnavailableError, match="All auto-tier TTS engines failed to preload"
    ):
        router.preload(engine="auto")


def test_router_preload_auto_no_backends_available() -> None:
    """Verifies router.preload raises TTSUnavailableError when no backends are available."""
    mock_piper = MagicMock()
    mock_piper.engine_name = "piper"
    mock_piper.is_available.return_value = False

    mock_espeak = MagicMock()
    mock_espeak.engine_name = "espeak"
    mock_espeak.is_available.return_value = False

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
    with pytest.raises(TTSUnavailableError, match="No TTS engine available"):
        router.preload(engine="auto")
