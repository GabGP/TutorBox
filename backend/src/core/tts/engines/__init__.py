"""Pluggable offline TTS engines registry."""

from core.tts.engines.espeak import EspeakBackend
from core.tts.engines.kokoro import KokoroBackend
from core.tts.engines.piper import PiperBackend
from core.tts.engines.qwen import QwenBackend
from core.tts.engines.sherpa import SherpaBackend

__all__ = [
    "EspeakBackend",
    "KokoroBackend",
    "PiperBackend",
    "QwenBackend",
    "SherpaBackend",
]
