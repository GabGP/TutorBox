"""Offline text-to-speech package for the classroom appliance (espeak-ng)."""

from core.tts.espeak import (
    TTSSynthesisError,
    TTSUnavailableError,
    resolve_binary,
    resolve_voice,
    synthesize_wav,
)
from core.tts.text import normalize_for_speech

__all__ = [
    "TTSSynthesisError",
    "TTSUnavailableError",
    "normalize_for_speech",
    "resolve_binary",
    "resolve_voice",
    "synthesize_wav",
]
