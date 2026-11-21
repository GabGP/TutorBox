"""disk, load and status: the rest of the readings and the thresholds that colour them."""

import shutil
from collections import namedtuple

import pytest

from core.system_health import thresholds
from core.system_health.disk import read_disk
from core.system_health.load import read_load_average, read_uptime_seconds
from core.system_health.status import (
    cpu_status,
    disk_status,
    gpu_status,
    memory_status,
    temperature_status,
)
from tests.core.system_health.fake_host import FakeHost

DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
GIBIBYTE = 1024**3


def test_disk_reports_the_partition_of_the_database_folder(tmp_path):
    disk = read_disk(tmp_path)

    assert disk is not None
    assert disk.total_gb > 0
    assert 0 <= disk.free_percent <= 100
    assert disk.free_gb <= disk.total_gb


def test_a_nearly_full_disk_is_warned_then_critical(monkeypatch, tmp_path):
    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda _path: DiskUsage(100 * GIBIBYTE, 92 * GIBIBYTE, 8 * GIBIBYTE),
    )
    warned = read_disk(tmp_path)

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda _path: DiskUsage(100 * GIBIBYTE, 97 * GIBIBYTE, 3 * GIBIBYTE),
    )
    critical = read_disk(tmp_path)

    assert warned is not None and warned.status == "warn"
    assert warned.free_percent == 8.0
    assert critical is not None and critical.status == "critical"


def test_a_folder_that_does_not_exist_gives_no_disk(tmp_path):
    assert read_disk(tmp_path / "missing") is None


def test_a_partition_that_reports_no_size_gives_no_disk(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: DiskUsage(0, 0, 0))

    assert read_disk(tmp_path) is None


def test_uptime_is_the_first_number_of_proc_uptime(tmp_path):
    FakeHost(tmp_path).write_uptime("98992.60 524771.45")

    assert read_uptime_seconds(tmp_path) == 98992.6


@pytest.mark.parametrize("text", ["", "   ", "not a number 12"])
def test_uptime_is_none_when_the_file_holds_no_number(tmp_path, text):
    FakeHost(tmp_path).write("proc/uptime", text)

    assert read_uptime_seconds(tmp_path) is None


def test_uptime_is_none_when_the_file_is_missing(tmp_path):
    assert read_uptime_seconds(tmp_path) is None


def test_load_average_is_the_three_minute_values(tmp_path):
    FakeHost(tmp_path).write_loadavg("3.32 4.45 3.74 3/859 558475")

    assert read_load_average(tmp_path) == [3.32, 4.45, 3.74]


@pytest.mark.parametrize("text", ["3.32 4.45", "3.32 x 3.74", ""])
def test_load_average_needs_all_three_numbers(tmp_path, text):
    FakeHost(tmp_path).write_loadavg(text)

    assert read_load_average(tmp_path) is None


def test_load_average_is_none_when_the_file_is_missing(tmp_path):
    assert read_load_average(tmp_path) is None


def test_temperature_warns_from_eighty_and_is_critical_from_ninety_five():
    assert temperature_status(None) == "unknown"
    assert temperature_status(79.9) == "ok"
    assert temperature_status(80.0) == "warn"
    assert temperature_status(94.9) == "warn"
    assert temperature_status(95.0) == "critical"


def test_cpu_warns_from_eighty_five_and_is_never_critical():
    assert cpu_status(None) == "unknown"
    assert cpu_status(84.9) == "ok"
    assert cpu_status(85.0) == "warn"
    assert cpu_status(100.0) == "warn"


def test_memory_is_warned_below_one_and_a_half_gigabytes_and_critical_below_three_quarters():
    assert memory_status(None) == "unknown"
    assert memory_status(1536.0) == "ok"
    assert memory_status(1535.9) == "warn"
    assert memory_status(768.0) == "warn"
    assert memory_status(767.9) == "critical"


def test_disk_is_warned_below_ten_percent_free_and_critical_below_five():
    assert disk_status(None) == "unknown"
    assert disk_status(10.0) == "ok"
    assert disk_status(9.9) == "warn"
    assert disk_status(5.0) == "warn"
    assert disk_status(4.9) == "critical"


def test_gpu_status_is_informational_and_never_warns():
    assert gpu_status(None) == "unknown"
    assert gpu_status(0.0) == "ok"
    assert gpu_status(100.0) == "ok"


def test_thresholds_are_the_documented_values():
    assert thresholds.TEMPERATURE_WARN_CELSIUS == 80.0
    assert thresholds.MEMORY_AVAILABLE_CRITICAL_MB == 768.0
    assert thresholds.DISK_FREE_CRITICAL_PERCENT == 5.0
