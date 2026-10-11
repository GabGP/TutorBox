"""Reads duration, sample rate and peak level out of WAV bytes."""

from __future__ import annotations

import io
import struct
import wave

PCM_SAMPLE_WIDTH_BYTES: int = 2  # 16-bit linear PCM (2 bytes per sample)
PCM_16BIT_MAX_FLOAT: float = 32768.0


def analyze_wav(wav_bytes: bytes) -> tuple[float, int, float]:
    """Extracts audio duration (s), sample rate (Hz), and normalized peak amplitude."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        num_channels = wav_file.getnchannels()
        raw_frames = wav_file.readframes(wav_file.getnframes())

    frame_size = sample_width * num_channels
    actual_frames = len(raw_frames) // frame_size if frame_size > 0 else 0
    duration = actual_frames / float(sample_rate) if sample_rate > 0 else 0.0

    if actual_frames == 0 or sample_width != PCM_SAMPLE_WIDTH_BYTES:
        return duration, sample_rate, 0.0

    sample_count = len(raw_frames) // PCM_SAMPLE_WIDTH_BYTES
    samples = struct.unpack(
        f"<{sample_count}h", raw_frames[: sample_count * PCM_SAMPLE_WIDTH_BYTES]
    )
    peak = max((abs(sample) for sample in samples), default=0.0) / PCM_16BIT_MAX_FLOAT
    return duration, sample_rate, peak
