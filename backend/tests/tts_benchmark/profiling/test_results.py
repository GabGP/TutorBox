"""Verifies the profile result records and the per-engine summary built from them."""

import dataclasses

import pytest

from tools.benchmark.tts.profiling.results import EngineStats, ProfileResult


def _run(**overrides) -> ProfileResult:
    """Builds a profile run on a plain 22050 Hz clip, with any field replaced by keyword."""
    fields = {
        "text": "hola",
        "latency_seconds": 1.0,
        "audio_duration_seconds": 2.0,
        "real_time_factor": 0.5,
        "sample_rate": 22050,
        "peak_amplitude": 0.25,
        "audio_byte_count": 2048,
    }
    fields.update(overrides)
    return ProfileResult(**fields)


def _stats(*runs: ProfileResult, provider: str = "cpu") -> EngineStats:
    """Wraps the runs in an engine record for the piper engine."""
    return EngineStats(engine="piper", runs=runs, wav_bytes=b"", provider=provider)


def _three_run_stats() -> EngineStats:
    """Cold run plus three warm runs, with the first and last run kept distinct."""
    cold = _run(
        latency_seconds=0.9,
        load_ms=120.5,
        rss_delta_mb=12.5,
        vram_delta_mb=3.25,
        rss_scope="process-tree",
        cold=True,
    )
    first_warm = _run(latency_seconds=0.2, real_time_factor=0.1)
    second_warm = _run(latency_seconds=0.4, real_time_factor=0.3)
    last = _run(
        latency_seconds=0.3,
        real_time_factor=0.2,
        peak_amplitude=0.5,
        sample_rate=24000,
        audio_byte_count=5000,
        load_ms=7.0,
        rss_delta_mb=99.0,
        vram_delta_mb=88.0,
    )
    return _stats(cold, first_warm, second_warm, last)


def test_profile_result_defaults_for_memory_and_cold_fields():
    """Verifies a profile run defaults to no load, no memory delta and a parent-only scope."""
    result = _run()
    assert result.load_ms == 0.0
    assert result.rss_delta_mb == 0.0
    assert result.vram_delta_mb == 0.0
    assert result.cold is False
    assert result.rss_scope == "parent-process-only"


def test_profile_result_is_frozen():
    """Verifies a profile run cannot be modified after it is built."""
    result = _run()
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.load_ms = 5.0


def test_engine_stats_provider_defaults_to_cpu():
    """Verifies an engine record reports the cpu provider when none is given."""
    stats = EngineStats(engine="piper", runs=(_run(),), wav_bytes=b"")
    assert stats.provider == "cpu"


def test_warm_runs_exclude_the_cold_first_run():
    """Verifies the warm view drops the first run and keeps the rest in order."""
    cold, first_warm, second_warm = _run(), _run(latency_seconds=2.0), _run()
    assert _stats(cold, first_warm, second_warm).warm == (first_warm, second_warm)


def test_warm_view_of_a_single_run_is_that_run():
    """Verifies a lone run is its own warm view, so one-run summaries still have figures."""
    only_run = _run(latency_seconds=0.6)
    assert _stats(only_run).warm == (only_run,)


def test_summary_has_exactly_the_documented_keys_in_order():
    """Verifies the summary reports the thirteen documented figures in their order."""
    assert list(_three_run_stats().summary()) == [
        "engine",
        "provider",
        "cold_first_s",
        "warm_p50_s",
        "warm_p95_s",
        "rtf_p50",
        "peak",
        "sr_hz",
        "wav_kb",
        "load_ms",
        "rss_delta_mb",
        "vram_delta_mb",
        "rss_scope",
    ]


def test_summary_values_for_a_three_warm_run_profile():
    """Verifies every summary figure for a cold run followed by three warm runs."""
    assert _three_run_stats().summary() == {
        "engine": "piper",
        "provider": "cpu",
        "cold_first_s": 0.9,
        "warm_p50_s": 0.3,
        "warm_p95_s": 0.4,
        "rtf_p50": 0.2,
        "peak": 0.5,
        "sr_hz": 24000,
        "wav_kb": 4.9,
        "load_ms": 120.5,
        "rss_delta_mb": 12.5,
        "vram_delta_mb": 3.25,
        "rss_scope": "process-tree",
    }


def test_cold_figures_and_memory_come_from_the_first_run():
    """Verifies cold latency, load, memory deltas and scope come from the first run only."""
    summary = _three_run_stats().summary()
    assert summary["cold_first_s"] == 0.9
    assert summary["load_ms"] == 120.5
    assert summary["rss_delta_mb"] == 12.5
    assert summary["vram_delta_mb"] == 3.25
    assert summary["rss_scope"] == "process-tree"


def test_peak_sample_rate_and_wav_size_come_from_the_last_run():
    """Verifies peak, sample rate and WAV size in KB come from the last run only."""
    summary = _three_run_stats().summary()
    assert summary["peak"] == 0.5
    assert summary["sr_hz"] == 24000
    assert summary["wav_kb"] == 4.9


def test_warm_median_of_an_even_count_averages_the_middle_pair():
    """Verifies the warm median averages the two middle latencies when the count is even."""
    stats = _stats(
        _run(),
        *(_run(latency_seconds=value) for value in (0.3, 0.1, 0.4, 0.2)),
    )
    summary = stats.summary()
    assert summary["warm_p50_s"] == pytest.approx(0.25)
    assert summary["warm_p95_s"] == 0.4


def test_warm_p95_is_the_largest_warm_latency_for_small_counts():
    """Verifies five warm runs report the largest latency as p95 and the middle one as p50."""
    stats = _stats(
        _run(),
        *(_run(latency_seconds=value) for value in (0.2, 0.9, 0.5, 0.1, 0.7)),
    )
    summary = stats.summary()
    assert summary["warm_p50_s"] == 0.5
    assert summary["warm_p95_s"] == 0.9


def test_warm_p95_takes_the_sorted_index_for_twenty_one_warm_runs():
    """Verifies p95 of 21 warm runs is the element at sorted index 19, not the maximum."""
    warm_latencies = [((index * 4) % 21 + 1) / 1000 for index in range(21)]
    stats = _stats(
        _run(latency_seconds=0.5),
        *(_run(latency_seconds=value) for value in warm_latencies),
    )
    summary = stats.summary()
    assert summary["warm_p95_s"] == 0.02
    assert max(warm_latencies) == 0.021


def test_latencies_round_to_three_decimals_and_rtf_to_four():
    """Verifies warm latency is rounded to 3 decimals and the RTF median to 4."""
    stats = _stats(
        _run(latency_seconds=0.5),
        _run(latency_seconds=0.1236, real_time_factor=0.123456),
    )
    summary = stats.summary()
    assert summary["warm_p50_s"] == 0.124
    assert summary["warm_p95_s"] == 0.124
    assert summary["rtf_p50"] == 0.1235


def test_single_run_summary_uses_that_run_for_warm_figures():
    """Verifies a one-run profile reports its only run as both cold and warm figures."""
    summary = _stats(_run(latency_seconds=0.6, real_time_factor=0.4)).summary()
    assert summary["cold_first_s"] == 0.6
    assert summary["warm_p50_s"] == 0.6
    assert summary["warm_p95_s"] == 0.6
    assert summary["rtf_p50"] == 0.4


def test_summary_reports_the_engine_provider():
    """Verifies the summary carries the provider the engine record was given."""
    assert _stats(_run(), provider="cuda").summary()["provider"] == "cuda"
