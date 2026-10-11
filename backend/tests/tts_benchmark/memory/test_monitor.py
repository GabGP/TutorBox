"""Verifies MemoryMonitor baselines, sampled peaks, deltas, scope and cleanup."""

import threading
from collections.abc import Callable

from tools.benchmark.tts.memory import monitor
from tools.benchmark.tts.memory.monitor import (
    DEFAULT_SAMPLE_INTERVAL_SECONDS,
    DISCRETE_VRAM_THRESHOLD_MB,
    SCOPE_DISCRETE_VRAM,
    SCOPE_HOST_ONLY,
    SCOPE_UMA_UNIFIED,
    MemoryMonitor,
)


class FakeNVMLTracker:
    """Stands in for NVMLTracker: serves VRAM readings and counts close calls."""

    def __init__(self, vram_reader: Callable[[], float]) -> None:
        self._vram_reader = vram_reader
        self.close_count = 0

    def get_vram_mb(self) -> float:
        return self._vram_reader()

    def close(self) -> None:
        self.close_count += 1


def install_fakes(
    monkeypatch,
    host_rss_reader: Callable[[], float],
    vram_reader: Callable[[], float],
    is_uma: bool = False,
) -> FakeNVMLTracker:
    """Replaces the host RSS, NVML and Jetson lookups seen by the monitor module."""
    tracker = FakeNVMLTracker(vram_reader)
    monkeypatch.setattr(monitor, "get_host_rss_mb", host_rss_reader)
    monkeypatch.setattr(monitor, "NVMLTracker", lambda: tracker)
    monkeypatch.setattr(monitor, "is_jetson_uma", lambda: is_uma)
    return tracker


def main_thread_then_sampler(
    main_thread_readings: list[float], sampler_reading: float
) -> Callable[[], float]:
    """Serves queued readings on the test thread and one fixed reading on the sampler.

    The test thread reads the baseline at construction and the final reading at exit,
    so those two calls are scripted; every other call comes from the sampler thread.
    """
    queued_readings = list(main_thread_readings)

    def read() -> float:
        if threading.current_thread() is threading.main_thread():
            return queued_readings.pop(0)
        return sampler_reading

    return read


def test_baselines_are_read_at_construction(monkeypatch):
    """Verifies the RSS and VRAM baselines and peaks are read when the monitor is built."""
    install_fakes(monkeypatch, host_rss_reader=lambda: 100.0, vram_reader=lambda: 40.0)
    memory_monitor = MemoryMonitor()
    assert memory_monitor.baseline_rss_mb == 100.0
    assert memory_monitor.baseline_vram_mb == 40.0
    assert memory_monitor.peak_rss_mb == 100.0
    assert memory_monitor.peak_vram_mb == 40.0
    assert memory_monitor.sample_interval_s == DEFAULT_SAMPLE_INTERVAL_SECONDS
    assert memory_monitor.is_uma is False


def test_sampling_thread_raises_the_peaks(monkeypatch):
    """Verifies readings served to the sampling thread raise both peaks."""
    sampler_served = threading.Event()

    def host_rss_reader() -> float:
        if threading.current_thread() is threading.main_thread():
            return 100.0
        sampler_served.set()
        return 300.0

    install_fakes(
        monkeypatch,
        host_rss_reader=host_rss_reader,
        vram_reader=main_thread_then_sampler([20.0, 20.0], sampler_reading=90.0),
    )
    with MemoryMonitor(sample_interval_s=0.0) as memory_monitor:
        assert sampler_served.wait(timeout=2)
    assert memory_monitor.peak_rss_mb == 300.0
    assert memory_monitor.peak_vram_mb == 90.0


def test_exit_reading_can_raise_the_peaks(monkeypatch):
    """Verifies the readings taken at exit can raise peaks the sampler never saw."""
    install_fakes(
        monkeypatch,
        host_rss_reader=main_thread_then_sampler([100.0, 250.0], sampler_reading=100.0),
        vram_reader=main_thread_then_sampler([20.0, 60.0], sampler_reading=20.0),
    )
    with MemoryMonitor(sample_interval_s=0.0) as memory_monitor:
        pass
    assert memory_monitor.peak_rss_mb == 250.0
    assert memory_monitor.rss_delta_mb == 150.0
    assert memory_monitor.peak_vram_mb == 60.0
    assert memory_monitor.vram_delta_mb == 40.0


def test_deltas_never_go_negative_when_readings_drop(monkeypatch):
    """Verifies readings that fall below the baseline leave the deltas at zero."""
    install_fakes(
        monkeypatch,
        host_rss_reader=main_thread_then_sampler([500.0, 100.0], sampler_reading=100.0),
        vram_reader=main_thread_then_sampler([50.0, 5.0], sampler_reading=5.0),
    )
    with MemoryMonitor(sample_interval_s=0.0) as memory_monitor:
        pass
    assert memory_monitor.peak_rss_mb == 500.0
    assert memory_monitor.rss_delta_mb == 0.0
    assert memory_monitor.vram_delta_mb == 0.0


def test_scope_is_uma_unified_on_a_jetson(monkeypatch):
    """Verifies a Jetson reports uma-unified even when the VRAM delta is large."""
    install_fakes(
        monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0, is_uma=True
    )
    memory_monitor = MemoryMonitor()
    memory_monitor.peak_vram_mb = 500.0
    assert memory_monitor.scope == SCOPE_UMA_UNIFIED


def test_scope_is_discrete_vram_above_the_threshold(monkeypatch):
    """Verifies a VRAM delta just above 10 MB reports discrete-vram."""
    install_fakes(monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0)
    memory_monitor = MemoryMonitor()
    memory_monitor.peak_vram_mb = DISCRETE_VRAM_THRESHOLD_MB + 0.5
    assert memory_monitor.scope == SCOPE_DISCRETE_VRAM


def test_scope_is_host_only_at_exactly_the_threshold(monkeypatch):
    """Verifies a VRAM delta of exactly 10 MB still reports host-only."""
    install_fakes(monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0)
    memory_monitor = MemoryMonitor()
    memory_monitor.peak_vram_mb = 10.0
    assert memory_monitor.scope == SCOPE_HOST_ONLY


def test_scope_is_host_only_below_the_threshold(monkeypatch):
    """Verifies a small VRAM delta on a discrete GPU machine reports host-only."""
    install_fakes(monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0)
    memory_monitor = MemoryMonitor()
    memory_monitor.peak_vram_mb = 9.0
    assert memory_monitor.scope == SCOPE_HOST_ONLY


def test_exit_closes_the_nvml_tracker(monkeypatch):
    """Verifies leaving the context closes the NVML tracker exactly once."""
    tracker = install_fakes(
        monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0
    )
    with MemoryMonitor(sample_interval_s=0.0):
        pass
    assert tracker.close_count == 1


def test_enter_returns_the_same_monitor(monkeypatch):
    """Verifies __enter__ hands back the monitor it was called on."""
    install_fakes(monkeypatch, host_rss_reader=lambda: 0.0, vram_reader=lambda: 0.0)
    memory_monitor = MemoryMonitor(sample_interval_s=0.0)
    with memory_monitor as entered_monitor:
        assert entered_monitor is memory_monitor
