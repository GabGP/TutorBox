"""Shared fixtures for the TTS benchmark tests: repo root on sys.path, WAV builder, fake router."""

import io
import struct
import sys
import wave
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def build_wav_bytes(
    frame_count: int = 2205,
    sample_rate: int = 22050,
    sample_width: int = 2,
    channel_count: int = 1,
    peak: int = 16384,
) -> bytes:
    """Builds in-memory WAV bytes whose samples alternate between +peak and -peak."""
    sample_count = frame_count * channel_count
    if sample_width == 2:
        samples = [peak if index % 2 == 0 else -peak for index in range(sample_count)]
        raw_frames = struct.pack(f"<{sample_count}h", *samples)
    else:
        raw_frames = bytes(sample_count * sample_width)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channel_count)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw_frames)
    return buffer.getvalue()


@pytest.fixture
def build_wav():
    """Returns the WAV builder so tests can ask for audio of a known shape."""
    return build_wav_bytes


class FakeRouter:
    """Stands in for the backend TTSRouter and records every call it receives."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.preload_milliseconds: float = 0.0
        self.backend: object | None = None
        self.wav_bytes: bytes = build_wav_bytes()
        self.preload_error: Exception | None = None

    def unload(self, engine: str | None = None) -> str:
        self.calls.append(("unload", engine))
        return engine or "all"

    def preload(
        self, engine: str | None = None, lang: str = "es", voice: str | None = None
    ) -> tuple[str | None, float]:
        self.calls.append(("preload", engine, lang, voice))
        if self.preload_error is not None:
            raise self.preload_error
        return engine, self.preload_milliseconds

    def clear_cache(self) -> None:
        self.calls.append(("clear_cache",))

    def synthesize(
        self,
        text: str,
        lang: str = "es",
        voice: str | None = None,
        backend: str | None = None,
    ) -> bytes:
        self.calls.append(("synthesize", text, lang, voice, backend))
        return self.wav_bytes

    def get_backend(self, engine: str | None) -> object | None:
        self.calls.append(("get_backend", engine))
        return self.backend


@pytest.fixture
def fake_router(monkeypatch):
    """Replaces the backend router seen by every profiling module with a FakeRouter."""
    from tools.benchmark.tts.profiling import backend_bridge

    router = FakeRouter()
    monkeypatch.setattr(backend_bridge, "get_tts_router", lambda: router)
    return router
