"""Abstract protocol for offline classroom TTS engines."""

from typing import Protocol, runtime_checkable

__all__ = ["TTSBackend"]


@runtime_checkable
class TTSBackend(Protocol):
    """Hardware-agnostic synthesis engine protocol for offline classroom speech."""

    @property
    def engine_name(self) -> str:
        """Returns the canonical engine identifier (e.g. 'piper', 'espeak')."""
        ...

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if the engine runtime and required models are usable."""
        ...

    def is_loaded(self) -> bool:
        """Returns True if model weights and resources are in memory."""
        ...

    def preload(self, voice: str | None = None) -> float:
        """Preloads model weights into memory, returning load time in milliseconds."""
        ...

    def unload(self) -> None:
        """Unloads model weights from memory to reclaim RAM."""
        ...

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text into standard RIFF/WAVE audio bytes."""
        ...
