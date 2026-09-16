"""Synthesis fallback policy for the Spanish TTS router."""

import logging

from core.config import get_settings
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.protocols import TTSBackend
from core.tts.router.selection import get_auto_backends, resolve_voice_for_backend

logger = logging.getLogger(__name__)


def synthesize_with_fallback(
    backends: dict[str, TTSBackend],
    target_backend: TTSBackend,
    text: str,
    lang: str,
    voice: str | None,
    espeak_backend: TTSBackend,
    *,
    explicit_backend: bool,
) -> bytes:
    """Synthesizes with the selected backend and applies the Spanish auto ladder."""
    target_voice = resolve_voice_for_backend(
        target_backend, lang, voice, espeak_backend=espeak_backend
    )
    try:
        return target_backend.synthesize(text, voice=target_voice)
    except (TTSSynthesisError, TTSUnavailableError) as error:
        settings = get_settings().tts
        if lang != "es" or explicit_backend or settings.engine.lower() != "auto":
            raise

        last_error: Exception = error
        for fallback_backend in get_auto_backends(backends, lang):
            if fallback_backend is target_backend:
                continue
            fallback_voice = resolve_voice_for_backend(
                fallback_backend, lang, voice, espeak_backend=espeak_backend
            )
            try:
                audio = fallback_backend.synthesize(text, voice=fallback_voice)
            except (TTSSynthesisError, TTSUnavailableError) as fallback_error:
                last_error = fallback_error
                continue
            logger.warning(
                "%s failed; fell back to %s: %s",
                target_backend.engine_name,
                fallback_backend.engine_name,
                error,
            )
            return audio
        raise last_error
