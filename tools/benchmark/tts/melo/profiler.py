"""Profiles MeloTTS cold load, warm synthesis latency, real-time factor and WAV properties."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tools.benchmark.tts.audio.wav_analysis import analyze_wav
from tools.benchmark.tts.melo.harness import MeloTTSHarness
from tools.benchmark.tts.memory.host_rss import get_host_rss_mb
from tools.benchmark.tts.profiling.rounding import (
    DECIMAL_PLACES_DURATION,
    DECIMAL_PLACES_LATENCY,
    DECIMAL_PLACES_METRIC,
    DECIMAL_PLACES_PEAK,
    DECIMAL_PLACES_RTF,
    DECIMAL_PLACES_WAV_KB,
)
from tools.benchmark.tts.shared.units import BYTES_PER_KB, MILLISECONDS_PER_SECOND

DEFAULT_WARM_REPEATS: int = 5
WARM_PERCENTILE: int = 95


def profile_melo(
    text: str,
    repeats: int = DEFAULT_WARM_REPEATS,
    provider: str = "cpu",
) -> dict[str, Any]:
    """Profiles MeloTTS cold load, warm latency, RTF, and acoustic properties."""
    harness = MeloTTSHarness(provider=provider)
    harness.unload()

    rss_before_mb = get_host_rss_mb()
    load_ms = harness.load()

    cold_start_time = time.perf_counter()
    wav_bytes = harness.synthesize(text)
    cold_synthesis_s = time.perf_counter() - cold_start_time
    rss_after_mb = get_host_rss_mb()

    cold_first_s = (load_ms / MILLISECONDS_PER_SECOND) + cold_synthesis_s
    rss_delta_mb = max(0.0, rss_after_mb - rss_before_mb)

    warm_latencies: list[float] = []
    for _ in range(max(1, repeats)):
        warm_start_time = time.perf_counter()
        wav_bytes = harness.synthesize(text)
        warm_latencies.append(time.perf_counter() - warm_start_time)

    duration, sample_rate, peak = analyze_wav(wav_bytes)
    warm_p50 = float(np.median(warm_latencies))
    warm_p95 = float(np.percentile(warm_latencies, WARM_PERCENTILE))
    rtf_p50 = warm_p50 / duration if duration > 0 else 0.0

    return {
        "engine": "melo",
        "provider": provider,
        "cold_first_s": round(cold_first_s, DECIMAL_PLACES_LATENCY),
        "warm_p50_s": round(warm_p50, DECIMAL_PLACES_LATENCY),
        "warm_p95_s": round(warm_p95, DECIMAL_PLACES_LATENCY),
        "rtf_p50": round(rtf_p50, DECIMAL_PLACES_RTF),
        "peak": round(peak, DECIMAL_PLACES_PEAK),
        "load_ms": round(load_ms, DECIMAL_PLACES_METRIC),
        "rss_delta_mb": round(rss_delta_mb, DECIMAL_PLACES_METRIC),
        "sr_hz": sample_rate,
        "wav_kb": round(len(wav_bytes) / BYTES_PER_KB, DECIMAL_PLACES_WAV_KB),
        "duration_s": round(duration, DECIMAL_PLACES_DURATION),
        "wav_bytes": wav_bytes,
    }
