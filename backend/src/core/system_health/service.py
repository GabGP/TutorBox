"""Assembles one health snapshot from the readers, cached for a few seconds."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from core.system_health.cache import TimedCache
from core.system_health.cpu import CpuMonitor
from core.system_health.disk import read_disk
from core.system_health.files import HOST_ROOT
from core.system_health.gpu import read_gpu
from core.system_health.load import read_load_average, read_uptime_seconds
from core.system_health.memory import read_memory
from core.system_health.models import ModelReading, SystemHealthSnapshot
from core.system_health.power import read_power_rails
from core.system_health.thermal import read_temperatures

__all__ = ["SystemHealthService"]

# Several open panels, each polling every few seconds, share one sample per two seconds.
SNAPSHOT_CACHE_SECONDS = 2.0


class SystemHealthService:
    """Reads the appliance once per cache window. Each reader is replaceable for tests."""

    def __init__(
        self,
        *,
        data_directory: Path,
        models_in_memory: Callable[[], list[ModelReading]],
        voices_loaded: Callable[[], list[str]],
        root: Path = HOST_ROOT,
        cpu_monitor: CpuMonitor | None = None,
        cache_seconds: float = SNAPSHOT_CACHE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._root = root
        self._data_directory = data_directory
        self._models_in_memory = models_in_memory
        self._voices_loaded = voices_loaded
        self._cpu = cpu_monitor or CpuMonitor(root)
        self._cache: TimedCache[SystemHealthSnapshot] = TimedCache(cache_seconds, clock)

    def snapshot(self) -> SystemHealthSnapshot:
        """The latest sample, read again once the cache window has passed."""
        return self._cache.get(self._sample)

    def invalidate(self) -> None:
        """Drops the cached snapshot, so the next reading is taken after a memory release."""
        self._cache.invalidate()

    def _sample(self) -> SystemHealthSnapshot:
        return SystemHealthSnapshot(
            sampled_at=datetime.now(UTC).isoformat(timespec="seconds"),
            cpu=self._cpu.read(),
            memory=read_memory(self._root),
            gpu=read_gpu(self._root),
            temperatures=read_temperatures(self._root),
            power=read_power_rails(self._root),
            disk=read_disk(self._data_directory),
            uptime_seconds=read_uptime_seconds(self._root),
            load_average=read_load_average(self._root),
            models=self._models_in_memory(),
            voices=self._voices_loaded(),
        )
