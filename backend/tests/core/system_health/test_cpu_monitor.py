"""CpuMonitor: the first reading takes two samples; later readings measure from the last one."""

from pathlib import Path

from core.system_health.cpu import CpuMonitor
from tests.core.system_health.fake_host import FakeHost


class SleepRecorder:
    def __init__(self) -> None:
        self.pauses: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.pauses.append(seconds)


def make_monitor(root: Path, sleep: SleepRecorder) -> CpuMonitor:
    return CpuMonitor(root, first_pause_seconds=0.2, sleep=sleep)


def test_the_first_reading_waits_between_two_samples_and_later_ones_do_not(tmp_path):
    host = FakeHost(tmp_path)
    host.write_cpu_stat(
        overall=[100, 0, 0, 900, 0, 0, 0, 0], cores={0: [100, 0, 0, 900, 0, 0, 0, 0]}
    )
    sleep = SleepRecorder()
    monitor = make_monitor(tmp_path, sleep)

    monitor.read()
    monitor.read()

    assert sleep.pauses == [0.2]


def test_each_reading_measures_the_time_since_the_previous_one(tmp_path):
    host = FakeHost(tmp_path)
    host.write_cpu_stat(
        overall=[100, 0, 0, 900, 0, 0, 0, 0], cores={0: [100, 0, 0, 900, 0, 0, 0, 0]}
    )
    monitor = make_monitor(tmp_path, SleepRecorder())
    monitor.read()

    # Since the first sample: +100 user and +100 idle, so 50% busy.
    host.write_cpu_stat(
        overall=[200, 0, 0, 1000, 0, 0, 0, 0], cores={0: [200, 0, 0, 1000, 0, 0, 0, 0]}
    )
    second = monitor.read()
    # Since the second sample: +300 user and nothing idle, so 100% busy.
    host.write_cpu_stat(
        overall=[500, 0, 0, 1000, 0, 0, 0, 0], cores={0: [500, 0, 0, 1000, 0, 0, 0, 0]}
    )
    third = monitor.read()

    assert second.usage_percent == 50.0
    assert second.status == "ok"
    assert third.usage_percent == 100.0
    assert third.per_core[0].usage_percent == 100.0


def test_a_busy_cpu_is_a_warning_and_each_core_has_its_clock(tmp_path):
    host = FakeHost(tmp_path)
    host.write_cpu_stat(
        overall=[100, 0, 0, 100, 0, 0, 0, 0],
        cores={0: [50, 0, 0, 50, 0, 0, 0, 0], 1: [50, 0, 0, 50, 0, 0, 0, 0]},
    )
    host.write_frequency_khz(0, "1190400")
    monitor = make_monitor(tmp_path, SleepRecorder())
    monitor.read()

    host.write_cpu_stat(
        overall=[190, 0, 0, 110, 0, 0, 0, 0],
        cores={0: [95, 0, 0, 55, 0, 0, 0, 0], 1: [95, 0, 0, 55, 0, 0, 0, 0]},
    )
    reading = monitor.read()

    assert reading.usage_percent == 90.0
    assert reading.status == "warn"
    assert [(core.index, core.freq_mhz) for core in reading.per_core] == [
        (0, 1190),
        (1, None),
    ]
    assert [core.usage_percent for core in reading.per_core] == [90.0, 90.0]


def test_an_unreadable_stat_file_gives_unknown_usage_without_an_error(tmp_path):
    monitor = make_monitor(tmp_path, SleepRecorder())

    reading = monitor.read()

    assert reading.usage_percent is None
    assert reading.per_core == []
    assert reading.status == "unknown"


def test_a_garbage_stat_file_gives_unknown_usage(tmp_path):
    FakeHost(tmp_path).write("proc/stat", "this is not /proc/stat\n")

    reading = make_monitor(tmp_path, SleepRecorder()).read()

    assert reading.usage_percent is None
    assert reading.per_core == []


def test_a_core_without_a_clock_reports_no_frequency(tmp_path):
    host = FakeHost(tmp_path)
    host.write_cpu_stat(
        overall=[10, 0, 0, 90, 0, 0, 0, 0], cores={3: [10, 0, 0, 90, 0, 0, 0, 0]}
    )
    host.write_frequency_khz(3, "not a number")
    monitor = make_monitor(tmp_path, SleepRecorder())

    reading = monitor.read()

    assert reading.per_core[0].index == 3
    assert reading.per_core[0].freq_mhz is None


def test_the_default_monitor_reads_this_machine():
    """The real /proc/stat, with the real pause: the first reading takes about 0.2 s."""
    reading = CpuMonitor().read()

    assert reading.status in {"ok", "warn", "unknown"}
