"""Timed single synthesis and the profile record built from the synthesized clip."""

from __future__ import annotations

import time
from typing import Any

from tools.benchmark.tts.audio.wav_analysis import analyze_wav
from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.profiling.results import (
    RSS_MEASUREMENT_SCOPE,
    ProfileResult,
)
from tools.benchmark.tts.profiling.rounding import (
    DECIMAL_PLACES_DURATION,
    DECIMAL_PLACES_METRIC,
    DECIMAL_PLACES_PEAK,
    DECIMAL_PLACES_RTF,
)


def synthesize_once(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    engine: str | None = None,
    router: Any | None = None,
) -> tuple[bytes, float]:
    """Synthesizes text after clearing the cache; returns (wav_bytes, latency_seconds)."""
    active_router = router or backend_bridge.get_tts_router()
    active_router.clear_cache()

    start_time = time.perf_counter()
    wav_bytes = active_router.synthesize(text, lang=lang, voice=voice, backend=engine)
    latency_seconds = time.perf_counter() - start_time
    return wav_bytes, latency_seconds


def make_profile_result(
    text: str,
    wav_bytes: bytes,
    latency_seconds: float,
    *,
    load_ms: float = 0.0,
    rss_delta_mb: float = 0.0,
    vram_delta_mb: float = 0.0,
    rss_scope: str = RSS_MEASUREMENT_SCOPE,
    cold: bool = False,
) -> ProfileResult:
    """Builds a ProfileResult from one synthesized clip and its timing."""
    duration_seconds, sample_rate, peak_amplitude = analyze_wav(wav_bytes)
    real_time_factor = (
        latency_seconds / duration_seconds if duration_seconds > 0 else 0.0
    )

    return ProfileResult(
        text=text,
        # A single run keeps four decimals; EngineStats.summary() rounds to three.
        latency_seconds=round(latency_seconds, DECIMAL_PLACES_RTF),
        audio_duration_seconds=round(duration_seconds, DECIMAL_PLACES_DURATION),
        real_time_factor=(
            round(real_time_factor, DECIMAL_PLACES_RTF) if duration_seconds > 0 else 0.0
        ),
        sample_rate=sample_rate,
        peak_amplitude=round(peak_amplitude, DECIMAL_PLACES_PEAK),
        audio_byte_count=len(wav_bytes),
        load_ms=round(load_ms, DECIMAL_PLACES_METRIC),
        rss_delta_mb=round(rss_delta_mb, DECIMAL_PLACES_METRIC),
        vram_delta_mb=round(vram_delta_mb, DECIMAL_PLACES_METRIC),
        cold=cold,
        rss_scope=rss_scope,
    )
