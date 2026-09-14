"""Latency and acoustic profiler for TutorBox offline speech synthesis."""

import io
import logging
import struct
import time
import wave
from dataclasses import dataclass

from core.tts.router import get_tts_router

__all__ = ["ProfileResult", "profile_speech_synthesis"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProfileResult:
    """Benchmark metrics for a single speech synthesis run."""

    text: str
    latency_seconds: float
    audio_duration_seconds: float
    real_time_factor: float
    sample_rate: int
    peak_amplitude: float
    audio_byte_count: int


def _analyze_wav(wav_bytes: bytes) -> tuple[float, int, float]:
    """Extracts audio duration, sample rate, and peak amplitude from WAV bytes."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        duration = frame_count / float(sample_rate) if sample_rate > 0 else 0.0
        frames = wav_file.readframes(frame_count)

    sample_count = len(frames) // 2
    if sample_count > 0:
        samples = struct.unpack(f"<{sample_count}h", frames)
        max_val = max(abs(s) for s in samples)
        peak = max_val / 32768.0
    else:
        peak = 0.0

    return duration, sample_rate, peak


def profile_speech_synthesis(
    text: str, lang: str = "es", voice: str | None = None
) -> ProfileResult:
    """Measures synthesis wall-clock latency, RTF, and acoustic properties."""
    router = get_tts_router()
    # Bypass cache for honest benchmarking
    cache_key = (text, lang, voice or "")
    router._cache.pop(cache_key, None)

    start_time = time.perf_counter()
    wav_bytes = router.synthesize(text, lang=lang, voice=voice)
    latency = time.perf_counter() - start_time

    duration, sample_rate, peak = _analyze_wav(wav_bytes)
    rtf = latency / duration if duration > 0 else 0.0

    return ProfileResult(
        text=text,
        latency_seconds=round(latency, 4),
        audio_duration_seconds=round(duration, 3),
        real_time_factor=round(rtf, 4),
        sample_rate=sample_rate,
        peak_amplitude=round(peak, 3),
        audio_byte_count=len(wav_bytes),
    )


def main() -> None:
    """CLI entrypoint for running benchmark on the edge appliance."""
    sample_text = (
        "Atención: 100 por ciento del grupo respondió un medio. "
        "Dividiste sólo el numerador entre 2. La respuesta correcta es tres cuartos."
    )
    print("Benchmarking TutorBox Neural TTS Pipeline...")
    res = profile_speech_synthesis(sample_text, lang="es")
    print(f"Latency:      {res.latency_seconds:.3f} s")
    print(f"Audio Length: {res.audio_duration_seconds:.2f} s")
    print(f"RTF:          {res.real_time_factor:.3f}x")
    print(f"Sample Rate:  {res.sample_rate} Hz")
    print(f"Peak Level:   {res.peak_amplitude:.2f} (normalized)")
    print(f"WAV Size:     {res.audio_byte_count / 1024:.1f} KB")


if __name__ == "__main__":  # pragma: no cover
    main()
