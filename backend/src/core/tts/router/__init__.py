"""Speech routing and fallback subpackage."""

from core.tts.router.router import (
    TTSRouter,
    clear_speech_cache,
    get_tts_router,
    synthesize_speech,
)
from core.tts.router.selection import _MAX_CACHE_ENTRIES, resolve_target_backend

__all__ = [
    "_MAX_CACHE_ENTRIES",
    "TTSRouter",
    "clear_speech_cache",
    "get_tts_router",
    "resolve_target_backend",
    "synthesize_speech",
]
