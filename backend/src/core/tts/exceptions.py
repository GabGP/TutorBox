"""Domain exceptions for TutorBox offline speech synthesis."""

__all__ = ["TTSError", "TTSSynthesisError", "TTSUnavailableError"]


class TTSError(RuntimeError):
    """Base exception for TutorBox speech synthesis errors."""


class TTSUnavailableError(TTSError):
    """espeak/piper/sherpa is disabled, not installed, or has no voice for the language."""


class TTSSynthesisError(TTSError):
    """TTS engine was found and executed, but failed or produced no audio."""
