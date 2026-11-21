"""SystemHealthService: one snapshot assembled from the readers, cached for two seconds."""

from datetime import datetime
from pathlib import Path

from core.system_health.cpu import CpuMonitor
from core.system_health.models import ModelReading, SystemHealthSnapshot
from core.system_health.service import SystemHealthService
from tests.core.system_health.fake_host import FakeHost, write_board


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def make_service(
    root: Path,
    data_directory: Path,
    clock: FakeClock | None = None,
    voices: list[str] | None = None,
) -> SystemHealthService:
    return SystemHealthService(
        root=root,
        data_directory=data_directory,
        models_in_memory=lambda: [ModelReading(name="qwen2.5:3b", gpu_percent=100)],
        voices_loaded=lambda: ["piper"] if voices is None else voices,
        cpu_monitor=CpuMonitor(
            root, first_pause_seconds=0, sleep=lambda _seconds: None
        ),
        clock=clock or FakeClock(),
    )


def test_the_snapshot_holds_every_reading_of_the_board(tmp_path):
    host_root = tmp_path / "host"
    write_board(FakeHost(host_root))

    snapshot = make_service(host_root, tmp_path).snapshot()

    assert isinstance(snapshot, SystemHealthSnapshot)
    datetime.fromisoformat(snapshot.sampled_at)
    assert snapshot.cpu.per_core[0].freq_mhz == 1190
    assert snapshot.memory is not None and snapshot.memory.total_mb == 7485.4
    assert snapshot.gpu is not None and snapshot.gpu.load_percent == 99.8
    assert [zone.zone for zone in snapshot.temperatures] == [
        "cpu-thermal",
        "gpu-thermal",
    ]
    assert [rail.rail for rail in snapshot.power] == ["VDD_IN", "VDD_CPU_GPU_CV"]
    assert snapshot.disk is not None and snapshot.disk.total_gb > 0
    assert snapshot.uptime_seconds == 98992.6
    assert snapshot.load_average == [3.32, 4.45, 3.74]
    assert [model.name for model in snapshot.models] == ["qwen2.5:3b"]
    assert snapshot.voices == ["piper"]


def test_a_machine_with_no_readable_files_still_gives_a_snapshot(tmp_path):
    empty_root = tmp_path / "empty"
    empty_root.mkdir()

    snapshot = make_service(empty_root, tmp_path, voices=[]).snapshot()

    assert snapshot.cpu.usage_percent is None
    assert snapshot.cpu.status == "unknown"
    assert snapshot.memory is None
    assert snapshot.gpu is None
    assert snapshot.temperatures == []
    assert snapshot.power == []
    assert snapshot.uptime_seconds is None
    assert snapshot.load_average is None
    assert snapshot.voices == []
    assert snapshot.models[0].name == "qwen2.5:3b"


def test_the_snapshot_is_shared_for_two_seconds_then_read_again(tmp_path):
    host_root = tmp_path / "host"
    host = FakeHost(host_root)
    host.write_meminfo(total_kib=7665092, available_kib=3466988)
    clock = FakeClock()
    service = make_service(host_root, tmp_path, clock=clock)
    first = service.snapshot()

    host.write_meminfo(total_kib=7665092, available_kib=500000)
    clock.now = 1.9
    within_window = service.snapshot()
    clock.now = 2.0
    after_window = service.snapshot()

    assert within_window is first
    assert first.memory is not None and first.memory.status == "ok"
    assert after_window.memory is not None and after_window.memory.status == "critical"


def test_the_default_root_reads_this_machine(tmp_path):
    """The real /proc and /sys of the machine the tests run on; only the shape is checked."""
    service = SystemHealthService(
        data_directory=tmp_path,
        models_in_memory=list,
        voices_loaded=list,
    )

    snapshot = service.snapshot()

    assert snapshot.cpu.status in {"ok", "warn", "unknown"}
    assert snapshot.disk is not None


def test_invalidate_drops_the_snapshot_so_the_next_one_is_fresh(tmp_path):
    host_root = tmp_path / "host"
    host = FakeHost(host_root)
    host.write_meminfo(total_kib=7665092, available_kib=3466988)
    service = make_service(host_root, tmp_path)
    service.snapshot()

    host.write_meminfo(total_kib=7665092, available_kib=500000)
    service.invalidate()

    fresh = service.snapshot().memory
    assert fresh is not None and fresh.status == "critical"
