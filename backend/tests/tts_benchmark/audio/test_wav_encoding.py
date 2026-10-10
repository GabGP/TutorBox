"""Verifies the mono 16-bit PCM WAV encoder: header fields, clipping, truncation and dtype handling."""

import io
import wave

import numpy as np

from tools.benchmark.tts.audio.wav_encoding import encode_mono_pcm16_wav

DEFAULT_SAMPLE_RATE = 44100


def decode_pcm16_frames(wav_bytes: bytes) -> list[int]:
    """Returns the little-endian 16-bit sample values stored in WAV bytes."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        raw_frames = wav_file.readframes(wav_file.getnframes())
    return np.frombuffer(raw_frames, dtype="<i2").tolist()


def test_output_opens_as_a_mono_16_bit_wav_at_the_requested_rate():
    """Verifies the bytes open as 1 channel, 2-byte samples, the given rate and frame count."""
    wav_bytes = encode_mono_pcm16_wav(np.zeros(1000), DEFAULT_SAMPLE_RATE)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == DEFAULT_SAMPLE_RATE
        assert wav_file.getnframes() == 1000


def test_samples_beyond_the_unit_range_are_clipped_to_full_scale():
    """Verifies values above 1.0 and below -1.0 are clipped to 32767 and -32767."""
    samples = np.array([1.5, -1.5, 2.0, -2.0, 1.0, -1.0])
    wav_bytes = encode_mono_pcm16_wav(samples, DEFAULT_SAMPLE_RATE)
    assert decode_pcm16_frames(wav_bytes) == [
        32767,
        -32767,
        32767,
        -32767,
        32767,
        -32767,
    ]


def test_half_scale_is_truncated_not_rounded():
    """Verifies 0.5 becomes 16383 (16383.5 truncated) and -0.5 becomes -16383."""
    wav_bytes = encode_mono_pcm16_wav(np.array([0.5, -0.5, 0.0]), DEFAULT_SAMPLE_RATE)
    assert decode_pcm16_frames(wav_bytes) == [16383, -16383, 0]


def test_float32_and_float64_inputs_give_identical_bytes():
    """Verifies float32 and float64 samples with the same values encode to the same WAV bytes."""
    values = [0.5, -0.25, 0.125, 0.0, 1.0, -1.0]
    from_float32 = encode_mono_pcm16_wav(
        np.array(values, dtype=np.float32), DEFAULT_SAMPLE_RATE
    )
    from_float64 = encode_mono_pcm16_wav(
        np.array(values, dtype=np.float64), DEFAULT_SAMPLE_RATE
    )
    assert from_float32 == from_float64
    assert decode_pcm16_frames(from_float64) == [16383, -8191, 4095, 0, 32767, -32767]


def test_empty_array_gives_a_valid_wav_with_no_frames():
    """Verifies an empty sample array still yields a readable mono WAV with zero frames."""
    wav_bytes = encode_mono_pcm16_wav(np.array([], dtype=np.float64), 22050)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050
        assert wav_file.getnframes() == 0
    assert decode_pcm16_frames(wav_bytes) == []
