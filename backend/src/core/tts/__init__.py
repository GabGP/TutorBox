"""Offline text-to-speech package for the TutorBox appliance."""

from core.tts.espeak import (
    EspeakBackend,
    TTSSynthesisError,
    TTSUnavailableError,
    resolve_binary,
    resolve_voice,
    synthesize_wav,
)
from core.tts.piper import PiperBackend, resolve_model_path
from core.tts.profiler import ProfileResult, profile_speech_synthesis
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
    "ProfileResult",
    "TTSBackend",
    "TTSRouter",
    "TTSSynthesisError",
    "TTSUnavailableError",
    "clear_speech_cache",
    "get_tts_router",
    "normalize_for_speech",
    "profile_speech_synthesis",
    "resolve_binary",
    "resolve_model_path",
    "resolve_voice",
    "synthesize_speech",
    "synthesize_wav",
]
