"""memory and gpu readers: present, missing and garbage files."""

from core.system_health.gpu import read_gpu
from core.system_health.memory import read_memory
from tests.core.system_health.fake_host import FakeHost


def test_memory_reads_totals_in_mebibytes_and_the_swap(tmp_path):
    FakeHost(tmp_path).write_meminfo(
        total_kib=7665092,
        available_kib=3466988,
        swap_total_kib=2048,
        swap_free_kib=1024,
    )

    memory = read_memory(tmp_path)

    assert memory is not None
    assert memory.total_mb == 7485.4
    assert memory.available_mb == 3385.7
    assert memory.used_percent == 54.8
    assert memory.swap_total_mb == 2.0
    assert memory.swap_used_mb == 1.0
    assert memory.status == "ok"


def test_memory_status_follows_the_memory_the_models_can_still_use(tmp_path):
    host = FakeHost(tmp_path)

    host.write_meminfo(total_kib=7665092, available_kib=1000000)
    warned = read_memory(tmp_path)
    host.write_meminfo(total_kib=7665092, available_kib=500000)
    critical = read_memory(tmp_path)

    assert warned is not None and warned.status == "warn"
    assert critical is not None and critical.status == "critical"


def test_memory_without_swap_lines_has_no_swap(tmp_path):
    FakeHost(tmp_path).write(
        "proc/meminfo", "MemTotal: 2048 kB\nMemAvailable: 1024 kB\n"
    )

    memory = read_memory(tmp_path)

    assert memory is not None
    assert memory.swap_total_mb == 0.0
    assert memory.swap_used_mb == 0.0


def test_swap_free_above_swap_total_never_shows_negative_use(tmp_path):
    FakeHost(tmp_path).write_meminfo(
        total_kib=2048, available_kib=1024, swap_total_kib=100, swap_free_kib=500
    )

    swap_memory = read_memory(tmp_path)
    assert swap_memory is not None and swap_memory.swap_used_mb == 0.0


def test_memory_is_none_when_the_file_is_missing_or_incomplete(tmp_path):
    assert read_memory(tmp_path) is None

    host = FakeHost(tmp_path)
    host.write("proc/meminfo", "MemTotal: 2048 kB\n")
    assert read_memory(tmp_path) is None

    host.write("proc/meminfo", "MemTotal: 0 kB\nMemAvailable: 0 kB\n")
    assert read_memory(tmp_path) is None


def test_memory_skips_garbage_lines(tmp_path):
    FakeHost(tmp_path).write(
        "proc/meminfo",
        "garbage without a colon\nMemTotal: many kB\nMemTotal: 4096 kB\n"
        "MemAvailable: 2048 kB\nHugePages_Total: 0\n",
    )

    memory = read_memory(tmp_path)

    assert memory is not None
    assert memory.total_mb == 4.0
    assert memory.available_mb == 2.0


def test_gpu_reads_load_and_both_clocks(tmp_path):
    FakeHost(tmp_path).write_gpu(
        load_per_mille="998", cur_hz="306000000", max_hz="918000000"
    )

    gpu = read_gpu(tmp_path)

    assert gpu is not None
    assert gpu.load_percent == 99.8
    assert gpu.freq_mhz == 306
    assert gpu.max_freq_mhz == 918
    assert gpu.status == "ok"


def test_gpu_with_only_a_clock_or_only_a_load_still_reports(tmp_path):
    host = FakeHost(tmp_path)
    host.write_gpu(load_per_mille="garbage", cur_hz="306000000", max_hz=None)
    only_clock = read_gpu(tmp_path)

    host = FakeHost(tmp_path / "other")
    host.write_gpu(load_per_mille="500", cur_hz=None, max_hz=None)
    only_load = read_gpu(tmp_path / "other")

    assert only_clock is not None
    assert only_clock.load_percent is None
    assert only_clock.status == "unknown"
    assert only_clock.freq_mhz == 306
    assert only_clock.max_freq_mhz is None
    assert only_load is not None
    assert only_load.load_percent == 50.0
    assert only_load.freq_mhz is None


def test_gpu_load_outside_zero_to_one_thousand_is_refused(tmp_path):
    FakeHost(tmp_path).write_gpu(load_per_mille="1500", cur_hz="306000000", max_hz=None)

    gpu = read_gpu(tmp_path)

    assert gpu is not None
    assert gpu.load_percent is None


def test_gpu_is_none_when_the_board_has_no_gpu_files(tmp_path):
    assert read_gpu(tmp_path) is None
