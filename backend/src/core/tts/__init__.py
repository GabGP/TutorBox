"""Offline text-to-speech package for the TutorBox appliance."""

from core.tts.audio import pcm_to_wav, samples_to_wav
from core.tts.constants import (
    DEFAULT_PIPER_SAMPLE_RATE_HZ,
    DEFAULT_TARGET_PEAK_AMPLITUDE,
    MILLISECONDS_PER_SECOND,
    PCM_16BIT_MAX_AMPLITUDE,
    PCM_CHANNELS_MONO,
    PCM_SAMPLE_WIDTH_BYTES,
)
from core.tts.engines import (
    EspeakBackend,
    KokoroBackend,
    PiperBackend,
    QwenBackend,
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
    "DEFAULT_PIPER_SAMPLE_RATE_HZ",
    "DEFAULT_TARGET_PEAK_AMPLITUDE",
    "MILLISECONDS_PER_SECOND",
    "PCM_16BIT_MAX_AMPLITUDE",
    "PCM_CHANNELS_MONO",
    "PCM_SAMPLE_WIDTH_BYTES",
    "EspeakBackend",
    "KokoroBackend",
    "PiperBackend",
    "QwenBackend",
    "SherpaBackend",
    "TTSBackend",
    "TTSError",
    "TTSRouter",
    "TTSSynthesisError",
    "TTSUnavailableError",
    "clear_speech_cache",
    "get_tts_router",
    "normalize_for_speech",
    "pcm_to_wav",
    "resolve_binary",
    "resolve_model_path",
    "resolve_voice",
    "samples_to_wav",
    "synthesize_speech",
    "synthesize_wav",
]
