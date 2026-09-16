"""Engine selection strategy and language-specific resolution for TTSRouter."""

import logging

from core.config import get_settings
from core.tts.exceptions import TTSUnavailableError
from core.tts.protocols import TTSBackend

__all__ = ["resolve_target_backend"]

logger = logging.getLogger(__name__)


def _resolve_quc_backend(
    target_engine: str,
    piper: TTSBackend,
    espeak: TTSBackend,
    voice_quc: str,
) -> TTSBackend:
    """Selects appropriate backend for Mayan K'iche' speech."""
    if target_engine == "espeak":
        if voice_quc and espeak.is_available(voice_quc):
            return espeak
        raise TTSUnavailableError("eSpeak cannot synthesize Mayan K'iche'.")
    if target_engine == "piper":
        if piper.is_available("quc"):
            return piper
        raise TTSUnavailableError("Piper K'iche' model is not installed.")
    if target_engine == "auto":
        if piper.is_available("quc"):
            return piper
        if voice_quc and espeak.is_available(voice_quc):
            return espeak
        raise TTSUnavailableError("No speech voice is configured for language 'quc'.")
    raise TTSUnavailableError(
        f"TTS engine '{target_engine}' is not registered or does not support 'quc'."
    )


def resolve_target_backend(
    backends: dict[str, TTSBackend],
    piper: TTSBackend,
    espeak: TTSBackend,
    lang: str = "es",
    engine: str | None = None,
) -> TTSBackend:
    """Resolves the active synthesis backend given language, engine override, and settings."""
    target_engine = (engine or get_settings().tts.engine).lower()

    if lang == "quc":
        settings = get_settings().tts
        return _resolve_quc_backend(target_engine, piper, espeak, settings.voice_quc)

    if engine:
        if target_engine in backends:
            backend = backends[target_engine]
            if backend.is_available(lang):
                return backend
            raise TTSUnavailableError(f"Engine '{engine}' is unavailable for '{lang}'.")
        raise TTSUnavailableError(
            f"TTS engine '{engine}' is not registered or not installed."
        )

    if target_engine in backends:
        backend = backends[target_engine]
        if backend.is_available(lang):
            return backend
        if target_engine == "piper" and lang == "es":
            raise TTSUnavailableError("Piper Spanish model is not installed.")
        raise TTSUnavailableError(
            f"Engine '{target_engine}' is unavailable for '{lang}'."
        )

    if target_engine != "auto":
        raise TTSUnavailableError(
            f"TTS engine '{target_engine}' is not registered or not installed."
        )

    # Default 'auto': prefer neural Piper, gracefully fallback to eSpeak
    if piper.is_available(lang):
        return piper
    logger.info("Piper voice unavailable for '%s'; falling back to eSpeak", lang)
    if espeak.is_available(lang):
        return espeak
    raise TTSUnavailableError(f"No TTS engine available for '{lang}'.")
