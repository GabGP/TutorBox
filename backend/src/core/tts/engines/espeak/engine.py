"""Offline classroom voice: espeak-ng synthesizing Latin American Spanish.

Formant synthesizer: zero model weights, ~10 MB RAM, sub-second synthesis.
Writes RIFF/WAVE stream to stdout for classroom audio playback.
"""

import logging
import shutil
import subprocess
import time

from core.config import get_settings
from core.tts.engines.espeak.cli import (
    BINARY_CANDIDATES,
    VOICE_FALLBACKS,
    resolve_binary,
    resolve_voice,
    synthesize_wav,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError

__all__ = [
    "BINARY_CANDIDATES",
    "VOICE_FALLBACKS",
    "EspeakBackend",
    "TTSSynthesisError",
    "TTSUnavailableError",
    "resolve_binary",
    "resolve_voice",
    "shutil",
    "subprocess",
    "synthesize_wav",
]

logger = logging.getLogger(__name__)


class EspeakBackend:
    """Formant speech synthesis backend conforming to TTSBackend protocol."""

    @property
    def engine_name(self) -> str:
        return "espeak"

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if espeak is installed and enabled."""
        settings = get_settings().tts
        if not settings.enabled:
            return False
        try:
            binary = resolve_binary(settings.binary)
            if voice:
                resolve_voice(binary, voice)
            return True
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        """Formant synthesizer has no in-memory weights; reports availability."""
        return self.is_available()

    def preload(self, voice: str | None = None) -> float:
        """Verifies binary and voice availability, returning duration in ms."""
        start_time = time.perf_counter()
        if not self.is_available(voice):
            raise TTSUnavailableError("eSpeak is unavailable or voice is missing.")
        return (time.perf_counter() - start_time) * 1000.0

    def unload(self) -> None:
        """No-op for CLI formant synthesis."""
        return

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text using espeak-ng formant synthesis."""
        return synthesize_wav(text, voice=voice)
