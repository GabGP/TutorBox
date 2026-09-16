"""eSpeak-NG formant TTS engine subpackage."""

from core.tts.engines.espeak.cli import (
    BINARY_CANDIDATES,
    VOICE_FALLBACKS,
    resolve_binary,
    resolve_voice,
    shutil,
    subprocess,
    synthesize_wav,
)
from core.tts.engines.espeak.engine import EspeakBackend

__all__ = [
    "BINARY_CANDIDATES",
    "VOICE_FALLBACKS",
    "EspeakBackend",
    "resolve_binary",
    "resolve_voice",
    "shutil",
    "subprocess",
    "synthesize_wav",
]
