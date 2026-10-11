"""Context manager that samples peak host RAM and GPU VRAM while a block runs."""

from __future__ import annotations

import threading
import time

from tools.benchmark.tts.memory.host_rss import get_host_rss_mb
from tools.benchmark.tts.memory.jetson import is_jetson_uma
from tools.benchmark.tts.memory.nvml import NVMLTracker

DEFAULT_SAMPLE_INTERVAL_SECONDS: float = 0.01
THREAD_JOIN_TIMEOUT_SECONDS: float = 1.0
DISCRETE_VRAM_THRESHOLD_MB: float = 10.0
SCOPE_UMA_UNIFIED = "uma-unified"
SCOPE_DISCRETE_VRAM = "discrete-vram"
SCOPE_HOST_ONLY = "host-only"


class MemoryMonitor:
    """Context manager for tracking peak Host RAM and GPU VRAM during synthesis."""

    def __init__(
        self, sample_interval_s: float = DEFAULT_SAMPLE_INTERVAL_SECONDS
    ) -> None:
        self.sample_interval_s = sample_interval_s
        self.nvml = NVMLTracker()
        self.is_uma = is_jetson_uma()

        self.baseline_rss_mb: float = get_host_rss_mb()
        self.baseline_vram_mb: float = self.nvml.get_vram_mb()

        self.peak_rss_mb: float = self.baseline_rss_mb
        self.peak_vram_mb: float = self.baseline_vram_mb

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)

    def _sample_loop(self) -> None:
        while not self._stop.is_set():
            rss = get_host_rss_mb()
            vram = self.nvml.get_vram_mb()
            self.peak_rss_mb = max(self.peak_rss_mb, rss)
            self.peak_vram_mb = max(self.peak_vram_mb, vram)
            time.sleep(self.sample_interval_s)

    # typing.Self needs Python 3.11, but the Jetson runs Python 3.10.
    def __enter__(self) -> MemoryMonitor:  # noqa: PYI034
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._stop.set()
        self._thread.join(timeout=THREAD_JOIN_TIMEOUT_SECONDS)
        final_rss = get_host_rss_mb()
        final_vram = self.nvml.get_vram_mb()
        self.peak_rss_mb = max(self.peak_rss_mb, final_rss)
        self.peak_vram_mb = max(self.peak_vram_mb, final_vram)
        self.nvml.close()

    @property
    def rss_delta_mb(self) -> float:
        """Returns peak host RAM delta in megabytes."""
        return max(0.0, self.peak_rss_mb - self.baseline_rss_mb)

    @property
    def vram_delta_mb(self) -> float:
        """Returns peak GPU VRAM delta in megabytes."""
        return max(0.0, self.peak_vram_mb - self.baseline_vram_mb)

    @property
    def scope(self) -> str:
        """Describes whether memory is UMA unified, discrete VRAM, or host RAM."""
        if self.is_uma:
            return SCOPE_UMA_UNIFIED
        if self.vram_delta_mb > DISCRETE_VRAM_THRESHOLD_MB:
            return SCOPE_DISCRETE_VRAM
        return SCOPE_HOST_ONLY
