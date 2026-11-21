"""CPU usage and per-core clocks. The monitor keeps the previous sample between readings."""

import time
from collections.abc import Callable
from pathlib import Path

from core.system_health.cpu_times import CpuSample, parse_cpu_sample, usage_between
from core.system_health.files import HOST_ROOT, read_int, read_text
from core.system_health.models import CoreReading, CpuReading
from core.system_health.status import cpu_status

__all__ = ["CpuMonitor"]

# The first reading needs a second sample to measure against; this is the wait between them.
FIRST_SAMPLE_PAUSE_SECONDS = 0.2


class CpuMonitor:
    """Each reading covers the time since the previous one, so the first call takes two samples."""

    def __init__(
        self,
        root: Path = HOST_ROOT,
        *,
        first_pause_seconds: float = FIRST_SAMPLE_PAUSE_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._root = root
        self._first_pause_seconds = first_pause_seconds
        self._sleep = sleep
        self._previous = CpuSample()
        self._has_previous_sample = False

    def read(self) -> CpuReading:
        """Samples /proc/stat, compares it with the previous sample and adds each core's clock."""
        if not self._has_previous_sample:
            self._previous = self._read_sample()
            self._has_previous_sample = True
            self._sleep(self._first_pause_seconds)
        current = self._read_sample()
        usage = usage_between(self._previous, current)
        self._previous = current
        per_core = [
            CoreReading(
                index=index,
                usage_percent=usage.per_core.get(index),
                freq_mhz=self._read_frequency_mhz(index),
            )
            for index in sorted(current.cores)
        ]
        return CpuReading(
            usage_percent=usage.overall,
            per_core=per_core,
            status=cpu_status(usage.overall),
        )

    def _read_sample(self) -> CpuSample:
        stat_text = read_text(self._root / "proc" / "stat")
        return CpuSample() if stat_text is None else parse_cpu_sample(stat_text)

    def _read_frequency_mhz(self, index: int) -> int | None:
        khz = read_int(
            self._root
            / "sys"
            / "devices"
            / "system"
            / "cpu"
            / f"cpu{index}"
            / "cpufreq"
            / "scaling_cur_freq"
        )
        return None if khz is None else khz // 1000
