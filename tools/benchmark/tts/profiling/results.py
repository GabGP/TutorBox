"""Result records of a TTS profiling run and their per-engine summary."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from tools.benchmark.tts.profiling.rounding import (
    DECIMAL_PLACES_LATENCY,
    DECIMAL_PLACES_METRIC,
    DECIMAL_PLACES_PEAK,
    DECIMAL_PLACES_RTF,
    DECIMAL_PLACES_WAV_KB,
)
from tools.benchmark.tts.shared.units import BYTES_PER_KB

PERCENTILE_95: float = 0.95
COLD_RUN_INDEX: int = 0
WARM_RUN_START_INDEX: int = 1
RSS_MEASUREMENT_SCOPE: str = "parent-process-only"


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
    load_ms: float = 0.0
    rss_delta_mb: float = 0.0
    vram_delta_mb: float = 0.0
    cold: bool = False
    rss_scope: str = RSS_MEASUREMENT_SCOPE


@dataclass(frozen=True)
class EngineStats:
    """Aggregated multi-run benchmark metrics for an engine."""

    engine: str
    runs: tuple[ProfileResult, ...]
    wav_bytes: bytes  # last warm run audio bytes for evaluation
    provider: str = "cpu"

    @property
    def warm(self) -> tuple[ProfileResult, ...]:
        """Returns only the warm synthesis runs (excluding cold first run)."""
        return self.runs[WARM_RUN_START_INDEX:] if len(self.runs) > 1 else self.runs

    def summary(self) -> dict[str, float | str | int]:
        """Calculates percentile latencies, RTF, peak level, and cold load footprint."""
        latencies = sorted(run.latency_seconds for run in self.warm)
        real_time_factors = sorted(run.real_time_factor for run in self.warm)
        first_run = self.runs[COLD_RUN_INDEX]
        last_run = self.runs[-1]
        p95_index = max(0, min(len(latencies) - 1, int(len(latencies) * PERCENTILE_95)))

        return {
            "engine": self.engine,
            "provider": self.provider,
            "cold_first_s": round(first_run.latency_seconds, DECIMAL_PLACES_LATENCY),
            "warm_p50_s": round(statistics.median(latencies), DECIMAL_PLACES_LATENCY),
            "warm_p95_s": round(latencies[p95_index], DECIMAL_PLACES_LATENCY),
            "rtf_p50": round(statistics.median(real_time_factors), DECIMAL_PLACES_RTF),
            "peak": round(last_run.peak_amplitude, DECIMAL_PLACES_PEAK),
            "sr_hz": last_run.sample_rate,
            "wav_kb": round(
                last_run.audio_byte_count / BYTES_PER_KB, DECIMAL_PLACES_WAV_KB
            ),
            "load_ms": round(first_run.load_ms, DECIMAL_PLACES_METRIC),
            "rss_delta_mb": round(first_run.rss_delta_mb, DECIMAL_PLACES_METRIC),
            "vram_delta_mb": round(first_run.vram_delta_mb, DECIMAL_PLACES_METRIC),
            "rss_scope": first_run.rss_scope,
        }
