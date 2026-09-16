"""Unit tests for audio packaging, calibration, and constants."""

import io
import struct
import wave

from core.tts.audio import pcm_to_wav, samples_to_wav
from core.tts.constants import (
    DEFAULT_PIPER_SAMPLE_RATE_HZ,
    DEFAULT_TARGET_PEAK_AMPLITUDE,
    PCM_16BIT_MAX_AMPLITUDE,
    PCM_CHANNELS_MONO,
    PCM_SAMPLE_WIDTH_BYTES,
)


def test_pcm_to_wav_format() -> None:
    raw_pcm = struct.pack("<3h", 1000, -2000, 3000)
    wav_bytes = pcm_to_wav(raw_pcm, DEFAULT_PIPER_SAMPLE_RATE_HZ)

    assert wav_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == PCM_CHANNELS_MONO
        assert wav_file.getsampwidth() == PCM_SAMPLE_WIDTH_BYTES
        assert wav_file.getframerate() == DEFAULT_PIPER_SAMPLE_RATE_HZ
        assert wav_file.getnframes() == 3
        read_pcm = wav_file.readframes(3)
        assert read_pcm == raw_pcm


def test_samples_to_wav_calibration() -> None:
    samples = [-1.0, -0.5, 0.0, 0.5, 1.0]
    wav_bytes = samples_to_wav(
        samples, DEFAULT_PIPER_SAMPLE_RATE_HZ, target_peak=0.5
    )

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frames = wav_file.readframes(len(samples))
        unpacked = struct.unpack(f"<{len(samples)}h", frames)
        max_val = max(abs(s) for s in unpacked)
        expected_max = int(0.5 * PCM_16BIT_MAX_AMPLITUDE)
        assert abs(max_val - expected_max) <= 1


def test_samples_to_wav_default_peak() -> None:
    samples = [-2.0, 2.0]
    wav_bytes = samples_to_wav(samples, DEFAULT_PIPER_SAMPLE_RATE_HZ)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frames = wav_file.readframes(len(samples))
        unpacked = struct.unpack(f"<{len(samples)}h", frames)
        max_val = max(abs(s) for s in unpacked)
        expected_max = int(
            DEFAULT_TARGET_PEAK_AMPLITUDE * PCM_16BIT_MAX_AMPLITUDE
        )
        assert abs(max_val - expected_max) <= 1


def test_samples_to_wav_empty() -> None:
    wav_bytes = samples_to_wav([], DEFAULT_PIPER_SAMPLE_RATE_HZ)
    assert wav_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnframes() == 0
