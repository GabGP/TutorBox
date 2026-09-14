"""Abstract protocol for offline classroom TTS engines."""

from typing import Protocol, runtime_checkable

__all__ = ["TTSBackend"]


@runtime_checkable
class TTSBackend(Protocol):
    """Hardware-agnostic synthesis engine protocol for offline classroom speech."""

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text into standard RIFF/WAVE audio bytes."""
        ...

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if the engine runtime and required models are usable."""
        ...
