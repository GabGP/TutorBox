"""Verifies the engine profile's router call order, cold and warm timing and memory reporting."""

import time
import types

import pytest

from tools.benchmark.tts.profiling import backend_bridge, engine_run
from tools.benchmark.tts.profiling.engine_run import (
    DEFAULT_PROFILE_REPEATS,
    profile_engine,
)

SAMPLE_TEXT = "hola"
ROUTER_CALLS_FOR_ONE_COLD_RUN = [
    ("unload", "piper"),
    ("preload", "piper", "es", None),
    ("clear_cache",),
    ("synthesize", SAMPLE_TEXT, "es", None, "piper"),
    ("get_backend", "piper"),
]


@pytest.fixture(autouse=True)
def clock_readings(monkeypatch):
    """Replaces time.perf_counter with a clock that advances a quarter second per reading."""
    readings: list[float] = []

    def fake_perf_counter() -> float:
        """Returns the next clock reading and records it."""
        reading = len(readings) * 0.25
        readings.append(reading)
        return reading

    monkeypatch.setattr(time, "perf_counter", fake_perf_counter)
    return readings


@pytest.fixture(autouse=True)
def monitor_events(monkeypatch):
    """Replaces MemoryMonitor with fixed readings and returns the log of its enter and exit."""
    events: list[str] = []

    class FakeMemoryMonitor:
        """Stands in for MemoryMonitor with fixed memory readings."""

        rss_delta_mb = 12.5
        vram_delta_mb = 3.25
        scope = "uma-unified"

        def __enter__(self):
            """Logs that the monitored block has started."""
            events.append("monitor-enter")
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            """Logs that the monitored block has ended."""
            events.append("monitor-exit")

    monkeypatch.setattr(engine_run, "MemoryMonitor", FakeMemoryMonitor)
    return events


@pytest.fixture(autouse=True)
def provider_requests(monkeypatch, fake_router):
    """Stands in for the provider lookup, answering cuda and logging how many router calls came first."""
    requests: list[tuple[str, int]] = []

    def fake_detect_engine_provider(engine: str) -> str:
        """Records the engine and the router call count at the time of the request."""
        requests.append((engine, len(fake_router.calls)))
        return "cuda"

    monkeypatch.setattr(
        backend_bridge, "detect_engine_provider", fake_detect_engine_provider
    )
    return requests


def test_router_call_log_for_three_repeats_is_cold_then_two_warm_turns(fake_router):
    """Verifies three repeats call the router as one cold turn followed by two warm turns."""
    profile_engine("piper", SAMPLE_TEXT, repeats=3)
    assert fake_router.calls == [
        *ROUTER_CALLS_FOR_ONE_COLD_RUN,
        ("clear_cache",),
        ("synthesize", SAMPLE_TEXT, "es", None, "piper"),
        ("clear_cache",),
        ("synthesize", SAMPLE_TEXT, "es", None, "piper"),
    ]


def test_default_repeats_gives_five_runs(fake_router):
    """Verifies profile_engine without a repeat count runs the default five syntheses."""
    stats = profile_engine("piper", SAMPLE_TEXT)
    synthesize_count = sum(1 for call in fake_router.calls if call[0] == "synthesize")
    assert DEFAULT_PROFILE_REPEATS == 5
    assert len(stats.runs) == 5
    assert synthesize_count == 5


@pytest.mark.parametrize("repeats", [0, 1], ids=["zero", "one"])
def test_zero_or_one_repeat_gives_only_the_cold_run(fake_router, repeats):
    """Verifies zero or one repeat leaves one cold run and no warm synthesis."""
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=repeats)
    assert [run.cold for run in stats.runs] == [True]
    assert fake_router.calls == ROUTER_CALLS_FOR_ONE_COLD_RUN


def test_positive_preload_time_is_the_cold_load_added_to_the_first_synthesis(
    fake_router,
):
    """Verifies a preload that reports load time sets the cold load and adds it to latency."""
    fake_router.preload_milliseconds = 120.5
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=1)
    cold_run = stats.runs[0]
    assert cold_run.cold is True
    assert cold_run.load_ms == 120.5
    assert cold_run.latency_seconds == 0.3705


def test_backend_figure_splits_the_cold_load_out_of_the_wall_time(fake_router):
    """Verifies the cold load is the wall time minus the backend's own synthesis time."""
    fake_router.backend = types.SimpleNamespace(last_synthesis_seconds=0.2)
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=1)
    assert stats.runs[0].load_ms == 50.0
    assert stats.runs[0].latency_seconds == 0.25


def test_warm_runs_report_the_backend_figure_instead_of_wall_time(fake_router):
    """Verifies warm runs report the backend's synthesis time when it is positive."""
    fake_router.backend = types.SimpleNamespace(last_synthesis_seconds=0.2)
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=3)
    assert [run.latency_seconds for run in stats.runs] == [0.25, 0.2, 0.2]


@pytest.mark.parametrize(
    "backend",
    [
        None,
        object(),
        types.SimpleNamespace(),
        types.SimpleNamespace(last_synthesis_seconds=0.0),
    ],
    ids=["no-backend", "no-attribute", "empty-namespace", "zero-figure"],
)
def test_warm_runs_keep_wall_time_without_a_positive_backend_figure(
    fake_router, backend
):
    """Verifies a missing, non-numeric or zero backend figure keeps the wall time."""
    fake_router.backend = backend
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=3)
    assert stats.runs[0].load_ms == 0.0
    assert stats.runs[0].latency_seconds == 0.25
    assert [run.latency_seconds for run in stats.runs[1:]] == [0.25, 0.25]


def test_warm_runs_are_warm_and_share_the_cold_memory_values(fake_router):
    """Verifies warm runs are not cold, have no load time and carry the cold memory figures."""
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=3)
    for run in stats.runs:
        assert (run.rss_delta_mb, run.vram_delta_mb, run.rss_scope) == (
            12.5,
            3.25,
            "uma-unified",
        )
    for warm_run in stats.runs[1:]:
        assert warm_run.cold is False
        assert warm_run.load_ms == 0.0


def test_wav_bytes_and_clip_sizes_follow_each_synthesis(
    monkeypatch, fake_router, build_wav
):
    """Verifies each run measures its own clip and the stats keep the last clip's audio."""
    clips = [build_wav(frame_count=count) for count in (1000, 2000, 3000)]
    remaining_clips = iter(clips)

    def synthesize_next_clip(text, lang="es", voice=None, backend=None):
        """Logs the call the way the fake router does, then returns the next clip."""
        fake_router.calls.append(("synthesize", text, lang, voice, backend))
        return next(remaining_clips)

    monkeypatch.setattr(fake_router, "synthesize", synthesize_next_clip)
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=3)
    assert stats.wav_bytes == clips[2]
    assert [run.audio_byte_count for run in stats.runs] == [len(c) for c in clips]


def test_engine_name_is_recorded_and_sent_to_the_router(fake_router):
    """Verifies the engine name is stored on the stats and used for the router calls."""
    stats = profile_engine("kokoro", SAMPLE_TEXT, repeats=1)
    assert stats.engine == "kokoro"
    assert fake_router.calls[0] == ("unload", "kokoro")


def test_provider_is_asked_once_after_all_syntheses(fake_router, provider_requests):
    """Verifies the provider comes from the bridge and is asked after the last synthesis."""
    stats = profile_engine("piper", SAMPLE_TEXT, repeats=3)
    assert stats.provider == "cuda"
    assert provider_requests == [("piper", 9)]


def test_preload_error_propagates_unchanged_and_the_monitor_is_exited(
    fake_router, monitor_events, provider_requests
):
    """Verifies a failing preload raises the same error, exits the monitor and skips the provider."""
    error = RuntimeError("x")
    fake_router.preload_error = error
    with pytest.raises(RuntimeError) as exc_info:
        profile_engine("piper", SAMPLE_TEXT)
    assert exc_info.value is error
    assert monitor_events == ["monitor-enter", "monitor-exit"]
    assert fake_router.calls == [("unload", "piper"), ("preload", "piper", "es", None)]
    assert provider_requests == []
