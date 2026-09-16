"""Offline text-to-speech package for the TutorBox appliance."""

from core.tts.engines import (
    EspeakBackend,
    PiperBackend,
    SherpaBackend,
)
from core.tts.engines.espeak import (
    resolve_binary,
    resolve_voice,
    synthesize_wav,
)
from core.tts.engines.piper import resolve_model_path
from core.tts.exceptions import (
    TTSError,
    TTSSynthesisError,
    TTSUnavailableError,
)
from core.tts.protocols import TTSBackend
from core.tts.router import (
    TTSRouter,
    clear_speech_cache,
    get_tts_router,
    synthesize_speech,
)
from core.tts.text import normalize_for_speech

__all__ = [
    "EspeakBackend",
    "PiperBackend",
    "SherpaBackend",
    "TTSBackend",
    "TTSError",
    "TTSRouter",
    "TTSSynthesisError",
    "TTSUnavailableError",
    "clear_speech_cache",
    "get_tts_router",
    "normalize_for_speech",
    "resolve_binary",
    "resolve_model_path",
    "resolve_voice",
    "synthesize_speech",
    "synthesize_wav",
]
