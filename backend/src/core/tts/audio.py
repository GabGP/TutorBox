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

__all__ = ["calibrate_wav_peak", "pcm_to_wav", "samples_to_wav"]


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


def calibrate_wav_peak(
    wav_bytes: bytes,
    target_peak: float = DEFAULT_TARGET_PEAK_AMPLITUDE,
) -> bytes:
    """Calibrates 16-bit PCM WAV audio bytes to target peak amplitude."""
    buf = io.BytesIO(wav_bytes)
    try:
        with wave.open(buf, "rb") as wav_file:
            channels = wav_file.getnchannels()
            width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
    except (wave.Error, EOFError):
        return wav_bytes

    if width != PCM_SAMPLE_WIDTH_BYTES or channels != PCM_CHANNELS_MONO or not frames:
        return wav_bytes

    int16_samples = array.array("h")
    int16_samples.frombytes(frames)
    max_amp = max((abs(s) for s in int16_samples), default=0)
    if max_amp == 0 or target_peak <= 0.0:
        return wav_bytes

    target_int = int(target_peak * PCM_16BIT_MAX_AMPLITUDE)
    scale = target_int / max_amp
    calibrated = array.array(
        "h",
        (
            int(
                max(
                    -PCM_16BIT_MAX_AMPLITUDE - 1,
                    min(PCM_16BIT_MAX_AMPLITUDE, s * scale),
                )
            )
            for s in int16_samples
        ),
    )
    return pcm_to_wav(calibrated.tobytes(), sample_rate)
