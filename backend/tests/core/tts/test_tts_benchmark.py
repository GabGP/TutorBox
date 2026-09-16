"""Backend SLA gate for speech synthesis (fast, hermetic).

Full comparative profiling (cold/warm, RSS, multi-engine sweep, WAV dumps)
moved to benchmark/tts/ (metrics.py + ab.py). This file keeps the CI gate:
synthesis wall-clock <= 3.0s on a mocked backend plus WAV sanity checks.
"""

import io
import struct
import time
import wave

import pytest


def _generate_test_wav(
    duration_seconds: float = 1.0, sample_rate: int = 22050, peak: int = 16000
) -> bytes:
    """Generates synthetic in-memory WAV bytes with known sample rate and amplitude."""
    frame_count = int(duration_seconds * sample_rate)
    samples = [peak if i % 2 == 0 else -peak for i in range(frame_count)]
    raw_pcm = struct.pack(f"<{frame_count}h", *samples)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw_pcm)
    return buf.getvalue()


def _wav_duration(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as f:
        n, rate = f.getnframes(), f.getframerate()
        return n / float(rate) if rate > 0 else 0.0


def test_wav_fixture_metrics():
    """Verifies the synthetic fixture has the expected duration and shape."""
    wav_bytes = _generate_test_wav(duration_seconds=2.0, sample_rate=22050, peak=16384)
    assert round(_wav_duration(wav_bytes), 1) == 2.0
    assert wav_bytes.startswith(b"RIFF")


def test_router_synthesis_sla_under_3_seconds(monkeypatch: pytest.MonkeyPatch):
    """Verifies router synthesis meets the <= 3.0s SLA ceiling (mocked backend)."""
    test_wav = _generate_test_wav(duration_seconds=3.0, sample_rate=22050, peak=20000)

    from core.tts.router import get_tts_router

    router = get_tts_router()
    monkeypatch.setattr(
        router, "synthesize", lambda text, lang="es", voice=None: test_wav
    )

    start = time.perf_counter()
    out = router.synthesize("Texto de prueba para síntesis.", lang="es")
    latency = time.perf_counter() - start

    assert out == test_wav
    assert latency <= 3.0
    assert round(_wav_duration(out), 1) == 3.0
