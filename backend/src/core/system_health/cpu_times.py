"""The CPU counters of /proc/stat and the busy share between two samples of them."""

from dataclasses import dataclass, field

__all__ = [
    "CpuSample",
    "CpuTimes",
    "CpuUsage",
    "parse_cpu_sample",
    "usage_between",
]

# /proc/stat lists user nice system idle iowait irq softirq steal; guest time is already in user.
COUNTERS_PER_LINE = 8
IDLE_INDEX = 3
IOWAIT_INDEX = 4
MINIMUM_COUNTERS = 5


@dataclass(frozen=True)
class CpuTimes:
    """Jiffies of one CPU line: idle (idle and iowait together) and all time."""

    idle: int
    total: int


@dataclass(frozen=True)
class CpuSample:
    """The aggregate line and one line per core. Both are empty when /proc/stat is unreadable."""

    overall: CpuTimes | None = None
    cores: dict[int, CpuTimes] = field(default_factory=dict)


@dataclass(frozen=True)
class CpuUsage:
    """Busy share in percent between two samples; None where the samples cannot say."""

    overall: float | None
    per_core: dict[int, float | None]


def parse_cpu_sample(stat_text: str) -> CpuSample:
    """Reads the cpu and cpuN lines of /proc/stat; any other or malformed line is skipped."""
    overall: CpuTimes | None = None
    cores: dict[int, CpuTimes] = {}
    for line in stat_text.splitlines():
        fields = line.split()
        if not fields or not fields[0].startswith("cpu"):
            continue
        times = _times_from_counters(fields[1:])
        if times is None:
            continue
        label = fields[0]
        if label == "cpu":
            overall = times
        elif label.removeprefix("cpu").isdigit():
            cores[int(label.removeprefix("cpu"))] = times
    return CpuSample(overall=overall, cores=cores)


def usage_between(before: CpuSample, after: CpuSample) -> CpuUsage:
    """Busy share since `before`: the non-idle part of the time that passed, in percent."""
    per_core = {
        index: _percent_between(before.cores.get(index), times)
        for index, times in after.cores.items()
    }
    return CpuUsage(
        overall=_percent_between(before.overall, after.overall),
        per_core=per_core,
    )


def _times_from_counters(values: list[str]) -> CpuTimes | None:
    if len(values) < MINIMUM_COUNTERS or not all(value.isdigit() for value in values):
        return None
    counters = [int(value) for value in values[:COUNTERS_PER_LINE]]
    idle = counters[IDLE_INDEX] + counters[IOWAIT_INDEX]
    return CpuTimes(idle=idle, total=sum(counters))


def _percent_between(before: CpuTimes | None, after: CpuTimes | None) -> float | None:
    if before is None or after is None:
        return None
    total_delta = after.total - before.total
    idle_delta = after.idle - before.idle
    # No time passed, or a counter went backwards (a reboot): the share is unknown.
    if total_delta <= 0 or not 0 <= idle_delta <= total_delta:
        return None
    return round(100 * (total_delta - idle_delta) / total_delta, 1)
