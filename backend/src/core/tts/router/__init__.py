"""Speech routing and fallback subpackage."""

from core.tts.router.router import TTSRouter, get_tts_router
from core.tts.router.selection import _MAX_CACHE_ENTRIES, resolve_target_backend

__all__ = [
    "_MAX_CACHE_ENTRIES",
    "TTSRouter",
    "clear_speech_cache",
    "get_tts_router",
    "resolve_target_backend",
    "synthesize_speech",
]


def synthesize_speech(text: str, lang: str = "es", voice: str | None = None) -> bytes:
    """Synthesizes speech using the global TTSRouter."""
    return get_tts_router().synthesize(text, lang=lang, voice=voice)


def clear_speech_cache() -> None:
    """Clears the global TTSRouter audio cache."""
    get_tts_router().clear_cache()
