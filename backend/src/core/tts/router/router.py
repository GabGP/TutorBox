"""Pluggable voice router with fallback and in-memory LRU audio caching."""
import logging
from typing import Any

from core.config import get_settings
from core.tts.engines import (
    EspeakBackend,
    KokoroBackend,
    PiperBackend,
    QwenBackend,
    SherpaBackend,
)
from core.tts.exceptions import TTSUnavailableError
from core.tts.protocols import TTSBackend
from core.tts.router.fallback import synthesize_with_fallback
from core.tts.router.selection import (
    get_auto_backends,
    get_engine_status,
    get_max_cache_entries,
    resolve_target_backend,
)

logger = logging.getLogger(__name__)

__all__ = [
    "TTSRouter",
    "get_tts_router",
]


class TTSRouter:
    """Routes speech synthesis requests across pluggable TTS engines with LRU caching."""

    def __init__(
        self,
        piper: TTSBackend | None = None,
        espeak: TTSBackend | None = None,
        sherpa: TTSBackend | None = None,
        kokoro: TTSBackend | None = None,
        qwen: TTSBackend | None = None,
        backends: dict[str, TTSBackend] | None = None,
    ) -> None:
        self.piper, self.espeak = piper or PiperBackend(), espeak or EspeakBackend()
        self.sherpa, self.kokoro = sherpa or SherpaBackend(), kokoro or KokoroBackend()
        self.qwen = qwen or QwenBackend()
        self._backends: dict[str, TTSBackend] = {
            "piper": self.piper,
            "espeak": self.espeak,
            "sherpa": self.sherpa,
            "kokoro": self.kokoro,
            "qwen3-tts": self.qwen,
            "qwen": self.qwen,
            **(backends or {}),
        }
        self._cache: dict[tuple[str, ...], bytes] = {}

    def clear_cache(self) -> None:
        """Clears cached synthesized WAV audio bytes."""
        self._cache.clear()

    def get_backend(self, engine_name: str | None) -> TTSBackend | None:
        """Looks up a registered backend by engine name."""
        if engine_name is None:
            return None
        return self._backends.get(engine_name.lower())

    def select_backend(self, lang: str = "es", engine: str | None = None) -> TTSBackend:
        """Selects the active backend based on language, override, or config."""
        return resolve_target_backend(
            self._backends, self.piper, self.espeak, lang=lang, engine=engine
        )

    def preload(
        self, engine: str | None = None, lang: str = "es", voice: str | None = None
    ) -> tuple[str, float]:
        """Preloads model weights for backend, returning (engine, load_ms).

        In auto mode, attempts backends in quality-first order, silently continuing
        to the next fallback engine if an engine fails to preload.
        """
        target_engine = (engine or get_settings().tts.engine).lower()
        if target_engine == "auto":
            candidates = get_auto_backends(self._backends, lang=lang)
            last_err: Exception | None = None
            for candidate in candidates:
                try:
                    return candidate.engine_name, candidate.preload(voice=voice or lang)
                except Exception as err:  # noqa: BLE001
                    logger.warning(
                        "Auto-tier TTS engine '%s' failed to preload: %s. Trying fallback.",
                        candidate.engine_name,
                        err,
                    )
                    last_err = err
            if last_err is not None:
                raise TTSUnavailableError(
                    f"All auto-tier TTS engines failed to preload for '{lang}': {last_err}"
                ) from last_err
            raise TTSUnavailableError(f"No TTS engine available for '{lang}'.")

        backend = self.select_backend(lang=lang, engine=engine)
        return backend.engine_name, backend.preload(voice=voice or lang)

    def unload(self, engine: str | None = None) -> str:
        """Unloads weights from memory for the target engine or all backends."""
        self.clear_cache()
        if engine:
            normalized = engine.lower()
            target = self._backends.get(normalized)
            if target:
                target.unload()
                return normalized
        for backend in self._backends.values():
            backend.unload()
        return engine or "all"

    def status(self, engine: str | None = None, lang: str = "es") -> dict[str, Any]:
        """Returns the readiness and model identifier of the target engine."""
        return get_engine_status(self.select_backend(lang=lang, engine=engine))

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
        audio = synthesize_with_fallback(
            self._backends,
            target_backend,
            text,
            lang,
            voice,
            self.espeak,
            explicit_backend=bool(backend),
        )

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
