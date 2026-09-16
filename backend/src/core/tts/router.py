"""Pluggable voice router with fallback and in-memory LRU audio caching."""

import logging
from typing import Any

from core.config import get_settings
from core.tts.espeak import EspeakBackend
from core.tts.exceptions import TTSUnavailableError
from core.tts.piper import PiperBackend
from core.tts.protocols import TTSBackend
from core.tts.router_selection import resolve_target_backend
from core.tts.sherpa import SherpaBackend

__all__ = [
    "TTSRouter",
    "clear_speech_cache",
    "get_tts_router",
    "synthesize_speech",
]

logger = logging.getLogger(__name__)
_MAX_CACHE_ENTRIES = 32


class TTSRouter:
    """Routes speech synthesis requests across pluggable TTS engines with LRU caching."""

    def __init__(
        self,
        piper: TTSBackend | None = None,
        espeak: TTSBackend | None = None,
        sherpa: TTSBackend | None = None,
        backends: dict[str, TTSBackend] | None = None,
    ) -> None:
        self.piper = piper or PiperBackend()
        self.espeak = espeak or EspeakBackend()
        self.sherpa = sherpa or SherpaBackend()
        self._backends: dict[str, TTSBackend] = dict(backends or {})
        self._backends.setdefault("piper", self.piper)
        self._backends.setdefault("espeak", self.espeak)
        self._backends.setdefault("sherpa", self.sherpa)
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
        load_ms = backend.preload(voice=voice or lang)
        return backend.engine_name, load_ms

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
        cfg = get_settings().tts
        mid_map = {"piper": cfg.piper_model_es, "sherpa": cfg.sherpa_model_es}
        return {
            "engine": backend.engine_name,
            "loaded": backend.is_loaded(),
            "model_id": mid_map.get(backend.engine_name, cfg.voice),
        }

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
        settings = get_settings().tts
        voice_to_use = voice or (
            settings.voice_quc
            if lang == "quc" and target_backend is self.espeak
            else (settings.voice if target_backend is self.espeak else lang)
        )

        try:
            audio = target_backend.synthesize(text, voice=voice_to_use)
        except TTSUnavailableError as err:
            can_fallback = lang == "es" and target_backend is self.piper and not backend
            if can_fallback and settings.engine.lower() == "auto":
                logger.warning("Piper failed; falling back to eSpeak: %s", err)
                audio = self.espeak.synthesize(text, voice=voice or settings.voice)
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
