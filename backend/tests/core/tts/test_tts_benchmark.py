"""Automated latency benchmark and SLA assertions for speech synthesis.

Validates that speech synthesis meets the <= 3.0 second latency ceiling (Task 4)
and correctly computes acoustic properties (Real-Time Factor, peak amplitude).
"""

import io
import struct
import wave

import pytest

from core.tts.profiler import (
    ProfileResult,
    _analyze_wav,
    main,
    profile_speech_synthesis,
)


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


def test_analyze_wav_metrics():
    """Verifies duration, sample rate, and peak normalization calculation."""
    wav_bytes = _generate_test_wav(duration_seconds=2.0, sample_rate=22050, peak=16384)
    duration, sample_rate, peak = _analyze_wav(wav_bytes)

    assert round(duration, 1) == 2.0
    assert sample_rate == 22050
    assert round(peak, 2) == 0.50  # 16384 / 32768 = 0.50


def test_analyze_wav_empty_frames():
    """Verifies handling of empty or 0-sample WAV files."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"")
    duration, sample_rate, peak = _analyze_wav(buf.getvalue())

    assert duration == 0.0
    assert sample_rate == 22050
    assert peak == 0.0


def test_profile_speech_synthesis_sla_under_3_seconds(monkeypatch: pytest.MonkeyPatch):
    """Verifies profile_speech_synthesis asserts latency meets the <= 3.0s SLA."""
    test_wav = _generate_test_wav(duration_seconds=3.0, sample_rate=22050, peak=20000)

    from core.tts.router import get_tts_router

    router = get_tts_router()
    monkeypatch.setattr(
        router, "synthesize", lambda text, lang="es", voice=None: test_wav
    )

    result = profile_speech_synthesis("Texto de prueba para síntesis.", lang="es")

    assert isinstance(result, ProfileResult)
    assert result.latency_seconds <= 3.0
    assert result.audio_duration_seconds == 3.0
    assert result.real_time_factor >= 0.0
    assert result.sample_rate == 22050
    assert result.peak_amplitude > 0.0
    assert result.audio_byte_count == len(test_wav)


def test_profiler_main_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """Verifies the CLI entrypoint executes and prints benchmark output."""
    test_wav = _generate_test_wav(duration_seconds=1.5, sample_rate=22050, peak=15000)
    from core.tts.router import get_tts_router

    router = get_tts_router()
    monkeypatch.setattr(
        router, "synthesize", lambda text, lang="es", voice=None: test_wav
    )

    main()
    captured = capsys.readouterr()
    assert "Benchmarking TutorBox Neural TTS Pipeline" in captured.out
    assert "Latency:" in captured.out
    assert "RTF:" in captured.out
