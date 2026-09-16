"""Audio packaging, amplitude calibration, and WAV encoding for TutorBox TTS."""

import array
import io
import wave
from collections.abc import Sequence

from core.tts.constants import (
    DEFAULT_TARGET_PEAK_AMPLITUDE,
    MAX_AUDIO_SAMPLE,
    MIN_AUDIO_SAMPLE,
    PCM_16BIT_MAX_AMPLITUDE,
    PCM_CHANNELS_MONO,
    PCM_SAMPLE_WIDTH_BYTES,
)

__all__ = ["pcm_to_wav", "samples_to_wav"]


def samples_to_wav(
    samples: Sequence[float],
    sample_rate: int,
    target_peak: float = DEFAULT_TARGET_PEAK_AMPLITUDE,
) -> bytes:
    """Converts float audio samples into RIFF/WAV bytes with calibrated peak amplitude."""
    max_amp = max((abs(sample) for sample in samples), default=0.0)
    scale = (target_peak / max_amp) if (max_amp > 0.0 and target_peak > 0.0) else 1.0

    int16_samples = array.array(
        "h",
        (
            int(
                max(MIN_AUDIO_SAMPLE, min(MAX_AUDIO_SAMPLE, s * scale))
                * PCM_16BIT_MAX_AMPLITUDE
            )
            for s in samples
        ),
    )
    return pcm_to_wav(int16_samples.tobytes(), sample_rate)


def pcm_to_wav(pcm_bytes: bytes | bytearray, sample_rate: int) -> bytes:
    """Encodes raw 16-bit linear PCM mono frames into standard RIFF/WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(PCM_CHANNELS_MONO)
        wav_file.setsampwidth(PCM_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buf.getvalue()
