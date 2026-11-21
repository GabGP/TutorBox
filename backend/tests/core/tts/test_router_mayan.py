"""Unit tests for engine choice in the Mayan languages (core/tts/router/mayan.py)."""

from unittest.mock import MagicMock

import pytest

from core.tts.exceptions import TTSUnavailableError
from core.tts.protocols import TTSBackend
from core.tts.router import TTSRouter
from core.tts.router.mayan import resolve_mayan_backend


def _backend(name: str, available: bool) -> MagicMock:
    backend = MagicMock()
    backend.engine_name = name
    backend.is_available.return_value = available
    return backend


def _resolve(engine, lang, *, mms=True, espeak=False, voice_quc=""):
    backends: dict[str, TTSBackend] = {"mms": _backend("mms", mms)}
    return resolve_mayan_backend(
        engine, lang, backends, _backend("espeak", espeak), voice_quc
    )


@pytest.mark.parametrize("lang", ["quc", "kek"])
def test_auto_prefers_the_mms_voice(lang):
    assert _resolve("auto", lang, espeak=True, voice_quc="quc").engine_name == "mms"


def test_auto_kiche_falls_back_to_a_configured_espeak_voice():
    espeak = _resolve("auto", "quc", mms=False, espeak=True, voice_quc="quc")
    assert espeak.engine_name == "espeak"


def test_auto_kiche_never_uses_espeak_without_a_kiche_voice():
    with pytest.raises(TTSUnavailableError, match="language 'quc'"):
        _resolve("auto", "quc", mms=False, espeak=True)


def test_auto_qeqchi_has_only_the_mms_voice():
    with pytest.raises(TTSUnavailableError, match="language 'kek'"):
        _resolve("auto", "kek", mms=False, espeak=True, voice_quc="quc")


@pytest.mark.parametrize(
    ("lang", "language_name"), [("quc", "Kʼicheʼ"), ("kek", "Qʼeqchiʼ")]
)
def test_explicit_mms(lang, language_name):
    assert _resolve("mms", lang).engine_name == "mms"
    with pytest.raises(TTSUnavailableError, match=f"MMS {language_name} voice"):
        _resolve("mms", lang, mms=False)


def test_explicit_mms_without_any_mms_backend():
    with pytest.raises(TTSUnavailableError, match="voice is not installed"):
        resolve_mayan_backend("mms", "kek", {}, _backend("espeak", True), "")


@pytest.mark.parametrize("engine", ["piper", "espeak", "qwen3-tts", "kokoro"])
def test_qeqchi_refuses_engines_without_a_qeqchi_voice(engine):
    with pytest.raises(TTSUnavailableError, match="does not support 'kek'"):
        _resolve(engine, "kek", espeak=True)


def test_explicit_kiche_engines():
    """eSpeak only with a configured Kʼicheʼ voice; Piper has none (removed 2026-11-21)."""
    espeak = _resolve("espeak", "quc", espeak=True, voice_quc="quc")
    assert espeak.engine_name == "espeak"
    with pytest.raises(TTSUnavailableError, match="eSpeak cannot synthesize"):
        _resolve("espeak", "quc", espeak=True)
    for engine in ("piper", "kokoro"):
        with pytest.raises(TTSUnavailableError, match="does not support 'quc'"):
            _resolve(engine, "quc")


def test_router_registers_the_mms_backend():
    router = TTSRouter(piper=_backend("piper", False), espeak=_backend("espeak", False))
    mms = router.get_backend("mms")
    assert mms is not None and mms.engine_name == "mms"
