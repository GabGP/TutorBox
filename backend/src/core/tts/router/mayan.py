"""Engine choice for the Mayan languages: Kʼicheʼ (quc) and Qʼeqchiʼ (kek).

A Mayan request never falls back to a Spanish voice: with no Mayan voice
installed the router raises TTSUnavailableError (the API answers 503).
Auto order for Kʼicheʼ: MMS, then a Piper Kʼicheʼ model, then eSpeak only when
TTS_VOICE_QUC names an installed voice. Qʼeqchiʼ has the MMS voice only.
"""

from core.tts.exceptions import TTSUnavailableError
from core.tts.protocols import TTSBackend

__all__ = ["MAYAN_LANGUAGES", "resolve_mayan_backend"]

MAYAN_LANGUAGES = ("quc", "kek")
_LANGUAGE_NAMES = {"quc": "Kʼicheʼ", "kek": "Qʼeqchiʼ"}


def _available(backend: TTSBackend | None, voice: str) -> TTSBackend | None:
    return backend if backend is not None and backend.is_available(voice) else None


def _resolve_kiche_backend(
    target_engine: str,
    mms: TTSBackend | None,
    piper: TTSBackend,
    espeak: TTSBackend,
    voice_quc: str,
) -> TTSBackend:
    espeak_voice = _available(espeak, voice_quc) if voice_quc else None
    if target_engine == "espeak":
        if espeak_voice:
            return espeak_voice
        raise TTSUnavailableError("eSpeak cannot synthesize Mayan K'iche'.")
    if target_engine == "piper":
        if piper.is_available("quc"):
            return piper
        raise TTSUnavailableError("Piper K'iche' model is not installed.")
    if target_engine == "auto":
        backend = _available(mms, "quc") or _available(piper, "quc") or espeak_voice
        if backend:
            return backend
        raise TTSUnavailableError("No speech voice is configured for language 'quc'.")
    raise TTSUnavailableError(
        f"TTS engine '{target_engine}' is not registered or does not support 'quc'."
    )


def resolve_mayan_backend(
    target_engine: str,
    lang: str,
    backends: dict[str, TTSBackend],
    piper: TTSBackend,
    espeak: TTSBackend,
    voice_quc: str,
) -> TTSBackend:
    """Picks the backend for a Mayan language, or raises TTSUnavailableError."""
    mms = backends.get("mms")
    if target_engine == "mms":
        if backend := _available(mms, lang):
            return backend
        raise TTSUnavailableError(
            f"The MMS {_LANGUAGE_NAMES[lang]} voice is not installed."
        )
    if lang == "quc":
        return _resolve_kiche_backend(target_engine, mms, piper, espeak, voice_quc)
    if target_engine == "auto":
        if backend := _available(mms, lang):
            return backend
        raise TTSUnavailableError(
            f"No speech voice is configured for language '{lang}'."
        )
    raise TTSUnavailableError(
        f"TTS engine '{target_engine}' is not registered or does not support '{lang}'."
    )
