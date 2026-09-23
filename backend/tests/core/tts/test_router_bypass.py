"""Unit tests for TTSRouter.synthesize bypass_cache (preview freshness)."""

from core.tts.router import TTSRouter

FAKE_WAV = b"RIFF-FAKE-WAV"


def _make_counting_router():
    """Builds a router whose piper backend counts synthesize calls."""
    from unittest.mock import MagicMock

    mock_piper = MagicMock()
    mock_piper.engine_name = "piper"
    mock_piper.is_available.return_value = True
    mock_espeak = MagicMock()
    mock_espeak.engine_name = "espeak"
    mock_espeak.is_available.return_value = False
    voices = {"calls": 0}

    def _synth(text, voice=None):
        voices["calls"] += 1
        return FAKE_WAV

    mock_piper.synthesize.side_effect = _synth
    router = TTSRouter(piper=mock_piper, espeak=mock_espeak)
    return router, voices


def test_synthesize_bypass_cache_renders_fresh_audio():
    """Bypassed previews never read or populate the LRU cache."""
    router, voices = _make_counting_router()

    router.synthesize("Hola", lang="es", backend="piper", bypass_cache=True)
    router.synthesize("Hola", lang="es", backend="piper", bypass_cache=True)

    assert voices["calls"] == 2
    assert router._cache == {}


def test_synthesize_without_bypass_uses_cache():
    """Default path keeps caching game speech as before."""
    router, voices = _make_counting_router()

    router.synthesize("Hola", lang="es", backend="piper")
    router.synthesize("Hola", lang="es", backend="piper")

    assert voices["calls"] == 1


def test_loaded_engines_lists_resident_backends_once():
    """Reports canonical engine names with weights in memory, deduplicated."""
    from unittest.mock import MagicMock

    from core.tts.router import TTSRouter

    loaded = MagicMock()
    loaded.engine_name = "piper"
    loaded.is_loaded.return_value = True
    idle = MagicMock()
    idle.engine_name = "espeak"
    idle.is_loaded.return_value = False
    router = TTSRouter(piper=loaded, espeak=idle)

    assert router.loaded_engines() == ["piper"]
