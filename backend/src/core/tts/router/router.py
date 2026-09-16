"""Pluggable voice router with fallback and in-memory LRU audio caching."""

import logging
from typing import Any

from core.config import get_settings
from core.tts.engines import EspeakBackend, KokoroBackend, PiperBackend, SherpaBackend
from core.tts.exceptions import TTSUnavailableError
from core.tts.protocols import TTSBackend
from core.tts.router.selection import (
    get_engine_status,
    get_max_cache_entries,
    resolve_target_backend,
    resolve_voice_for_backend,
)

__all__ = [
    "TTSRouter",
    "clear_speech_cache",
    "get_tts_router",
    "synthesize_speech",
]

logger = logging.getLogger(__name__)


class TTSRouter:
    """Routes speech synthesis requests across pluggable TTS engines with LRU caching."""

    def __init__(
        self,
        piper: TTSBackend | None = None,
        espeak: TTSBackend | None = None,
        sherpa: TTSBackend | None = None,
        kokoro: TTSBackend | None = None,
        backends: dict[str, TTSBackend] | None = None,
    ) -> None:
        self.piper = piper or PiperBackend()
        self.espeak = espeak or EspeakBackend()
        self.sherpa = sherpa or SherpaBackend()
        self.kokoro = kokoro or KokoroBackend()
        self._backends: dict[str, TTSBackend] = {
            "piper": self.piper,
            "espeak": self.espeak,
            "sherpa": self.sherpa,
            "kokoro": self.kokoro,
            **(backends or {}),
        }
        self._cache: dict[tuple[str, ...], bytes] = {}

    def clear_cache(self) -> None:
        """Clears cached synthesized WAV audio bytes."""
        self._cache.clear()

    def get_backend(self, engine_name: str) -> TTSBackend | None:
        """Looks up a registered backend by engine name."""
        return self._backends.get(engine_name.lower())

    def select_backend(self, lang: str = "es", engine: str | None = None) -> TTSBackend:
        """Selects the active backend based on language, override, or config."""
        return resolve_target_backend(
            self._backends, self.piper, self.espeak, lang=lang, engine=engine
        )

    def preload(
        self, engine: str | None = None, lang: str = "es", voice: str | None = None
    ) -> tuple[str, float]:
        """Preloads model weights for backend, returning (engine, load_ms)."""
        backend = self.select_backend(lang=lang, engine=engine)
        return backend.engine_name, backend.preload(voice=voice or lang)

    def unload(self, engine: str | None = None) -> str:
        """Unloads weights from memory for the target engine or all backends."""
        self.clear_cache()
        if engine and engine.lower() in self._backends:
            self._backends[engine.lower()].unload()
            return engine.lower()
        for backend in self._backends.values():
            backend.unload()
        return engine or "all"

    def status(self, engine: str | None = None, lang: str = "es") -> dict[str, Any]:
        """Returns the readiness and model identifier of the target engine."""
        backend = self.select_backend(lang=lang, engine=engine)
        return get_engine_status(backend)

    def synthesize(
        self,
        text: str,
        lang: str = "es",
        voice: str | None = None,
        backend: str | None = None,
    ) -> bytes:
        """Synthesizes text into WAV bytes, leveraging in-memory LRU cache."""
        cache_key = (
            (text, lang, voice or "")
            if not backend
            else (text, lang, voice or "", backend)
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        target_backend = self.select_backend(lang=lang, engine=backend)
        voice_to_use = resolve_voice_for_backend(
            target_backend, lang, voice, espeak_backend=self.espeak
        )

        try:
            audio = target_backend.synthesize(text, voice=voice_to_use)
        except TTSUnavailableError as err:
            settings = get_settings().tts
            can_fallback = lang == "es" and target_backend is self.piper and not backend
            if can_fallback and settings.engine.lower() == "auto":
                logger.warning("Piper failed; falling back to eSpeak: %s", err)
                audio = self.espeak.synthesize(text, voice=voice or settings.voice)
            else:
                raise

        if len(self._cache) >= get_max_cache_entries():
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
