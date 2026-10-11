"""Verifies the single-run profiler times one synthesis inside the memory monitor."""

import time

import pytest

from tools.benchmark.tts.profiling import single_run
from tools.benchmark.tts.profiling.single_run import profile_speech_synthesis

SAMPLE_TEXT = "hola"


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

    monkeypatch.setattr(single_run, "MemoryMonitor", FakeMemoryMonitor)
    return events


def test_result_carries_the_monitor_memory_values_and_scope(fake_router):
    """Verifies the monitor's RSS and VRAM deltas and its scope are copied onto the result."""
    result = profile_speech_synthesis(SAMPLE_TEXT)
    assert result.text == SAMPLE_TEXT
    assert result.latency_seconds == 0.25
    assert result.real_time_factor == 2.5
    assert result.rss_delta_mb == 12.5
    assert result.vram_delta_mb == 3.25
    assert result.rss_scope == "uma-unified"
    assert result.cold is False
    assert result.load_ms == 0.0


def test_language_voice_and_engine_are_forwarded_to_the_router(fake_router):
    """Verifies lang, voice and engine reach the router's synthesize call."""
    profile_speech_synthesis(SAMPLE_TEXT, lang="en", voice="amy", engine="piper")
    assert fake_router.calls == [
        ("clear_cache",),
        ("synthesize", SAMPLE_TEXT, "en", "amy", "piper"),
    ]


def test_defaults_are_spanish_with_no_voice_and_no_engine(fake_router):
    """Verifies the language defaults to es and the voice and engine to None."""
    profile_speech_synthesis(SAMPLE_TEXT)
    assert fake_router.calls == [
        ("clear_cache",),
        ("synthesize", SAMPLE_TEXT, "es", None, None),
    ]


def test_synthesis_runs_between_monitor_enter_and_exit(
    monkeypatch, fake_router, monitor_events
):
    """Verifies the synthesis happens inside the monitor block, after enter and before exit."""
    original_synthesize = fake_router.synthesize

    def logged_synthesize(*args, **kwargs):
        """Logs the synthesis in the monitor event log, then runs it."""
        monitor_events.append("synthesize")
        return original_synthesize(*args, **kwargs)

    monkeypatch.setattr(fake_router, "synthesize", logged_synthesize)
    profile_speech_synthesis(SAMPLE_TEXT)
    assert monitor_events == ["monitor-enter", "synthesize", "monitor-exit"]
