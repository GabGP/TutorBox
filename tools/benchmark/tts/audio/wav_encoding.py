"""Encodes float audio samples as 16-bit mono PCM WAV bytes."""

from __future__ import annotations

import io
import wave

import numpy as np

from tools.benchmark.tts.audio.wav_analysis import PCM_SAMPLE_WIDTH_BYTES

PCM_16BIT_MAX_INT: float = 32767.0
MONO_CHANNEL_COUNT: int = 1


def encode_mono_pcm16_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    """Clips float samples to [-1, 1] and returns the bytes of an in-memory 16-bit mono WAV."""
    int16_samples = (np.clip(samples, -1.0, 1.0) * PCM_16BIT_MAX_INT).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(MONO_CHANNEL_COUNT)
        wav_file.setsampwidth(PCM_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int16_samples.tobytes())
    return buffer.getvalue()
