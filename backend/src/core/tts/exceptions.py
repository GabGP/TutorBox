"""Domain exceptions for TutorBox offline speech synthesis."""

__all__ = ["TTSSynthesisError", "TTSUnavailableError"]


class TTSUnavailableError(RuntimeError):
    """espeak/piper is disabled, not installed, or has no voice for the language."""


class TTSSynthesisError(RuntimeError):
    """TTS engine was found and executed, but failed or produced no audio."""
