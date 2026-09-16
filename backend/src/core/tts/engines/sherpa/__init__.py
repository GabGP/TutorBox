"""Sherpa-ONNX neural TTS engine subpackage."""

from core.tts.engines.sherpa.engine import SherpaBackend
from core.tts.engines.sherpa.models import resolve_sherpa_paths, samples_to_wav

__all__ = [
    "SherpaBackend",
    "resolve_sherpa_paths",
    "samples_to_wav",
]
