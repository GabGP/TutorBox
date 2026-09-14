"""Pluggable voice router with fallback and in-memory LRU audio caching."""

import logging

from core.config import get_settings
from core.tts.espeak import EspeakBackend, TTSUnavailableError
from core.tts.piper import PiperBackend
from core.tts.protocols import TTSBackend

__all__ = [
    "TTSRouter",
    "clear_speech_cache",
    "get_tts_router",
    "synthesize_speech",
]

logger = logging.getLogger(__name__)
_MAX_CACHE_ENTRIES = 32


class TTSRouter:
    """Routes speech synthesis requests to Piper or eSpeak with LRU caching."""

    def __init__(
        self,
        piper: TTSBackend | None = None,
        espeak: TTSBackend | None = None,
    ) -> None:
        self.piper = piper or PiperBackend()
        self.espeak = espeak or EspeakBackend()
        self._cache: dict[tuple[str, str, str], bytes] = {}

    def clear_cache(self) -> None:
        """Clears cached synthesized WAV audio bytes."""
        self._cache.clear()

    def select_backend(self, lang: str = "es") -> TTSBackend:
        """Selects the active backend based on language and configured TTS_ENGINE."""
        settings = get_settings().tts
        engine = settings.engine.lower()

        if lang == "quc":
            if engine == "espeak":
                if settings.voice_quc and self.espeak.is_available(settings.voice_quc):
                    return self.espeak
                raise TTSUnavailableError("eSpeak cannot synthesize Mayan K'iche'.")
            if self.piper.is_available("quc"):
                return self.piper
            if settings.voice_quc and self.espeak.is_available(settings.voice_quc):
                return self.espeak
            raise TTSUnavailableError(
                f"No speech voice is configured for language '{lang}'."
            )

        if engine == "espeak":
            return self.espeak
        if engine == "piper":
            if self.piper.is_available(lang):
                return self.piper
            raise TTSUnavailableError("Piper Spanish model is not installed.")

        # Default 'auto': prefer neural Piper, gracefully fallback to eSpeak
        if self.piper.is_available(lang):
            return self.piper
        logger.info("Piper voice unavailable for '%s'; falling back to eSpeak", lang)
        return self.espeak

    def synthesize(
        self, text: str, lang: str = "es", voice: str | None = None
    ) -> bytes:
        """Synthesizes text into WAV bytes, leveraging in-memory LRU cache."""
        cache_key = (text, lang, voice or "")
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        backend = self.select_backend(lang)
        voice_to_use = voice
        if not voice_to_use:
            settings = get_settings().tts
            if backend is self.espeak:
                voice_to_use = settings.voice_quc if lang == "quc" else settings.voice
            else:
                voice_to_use = lang

        try:
            audio = backend.synthesize(text, voice=voice_to_use)
        except TTSUnavailableError as err:
            if lang == "es" and backend is self.piper:
                logger.warning("Piper failed; falling back to eSpeak: %s", err)
                espeak_voice = voice or get_settings().tts.voice
                audio = self.espeak.synthesize(text, voice=espeak_voice)
            else:
                raise

        if len(self._cache) >= _MAX_CACHE_ENTRIES:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = audio
        return audio


_ROUTER_INSTANCE: TTSRouter | None = None


def get_tts_router() -> TTSRouter:
    """Returns the singleton TTSRouter instance."""
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = TTSRouter()
    return _ROUTER_INSTANCE


def synthesize_speech(text: str, lang: str = "es", voice: str | None = None) -> bytes:
    """Synthesizes speech using the global TTSRouter."""
    return get_tts_router().synthesize(text, lang=lang, voice=voice)


def clear_speech_cache() -> None:
    """Clears the global TTSRouter audio cache."""
    get_tts_router().clear_cache()
