"""The integrated GPU: its load (per mille, from the driver) and its clock (devfreq, in Hz)."""

from pathlib import Path

from core.system_health.files import HOST_ROOT, first_match, read_int
from core.system_health.models import GpuReading
from core.system_health.status import gpu_status

__all__ = ["read_gpu"]

# The driver reports load in per mille: 1000 is a fully busy GPU.
LOAD_PER_MILLE_LIMIT = 1000
HERTZ_PER_MEGAHERTZ = 1_000_000


def read_gpu(root: Path = HOST_ROOT) -> GpuReading | None:
    """The GPU's load and clocks. None when the board has no readable GPU at all."""
    load_percent = _read_load_percent(root)
    device_dir = first_match(root, "sys/class/devfreq/*.gpu")
    freq_mhz = _read_mhz(device_dir, "cur_freq")
    max_freq_mhz = _read_mhz(device_dir, "max_freq")
    if load_percent is None and freq_mhz is None and max_freq_mhz is None:
        return None
    return GpuReading(
        load_percent=load_percent,
        freq_mhz=freq_mhz,
        max_freq_mhz=max_freq_mhz,
        status=gpu_status(load_percent),
    )


def _read_load_percent(root: Path) -> float | None:
    load_file = first_match(root, "sys/devices/platform/bus@0/*.gpu/load")
    if load_file is None:
        return None
    load_per_mille = read_int(load_file)
    if load_per_mille is None or not 0 <= load_per_mille <= LOAD_PER_MILLE_LIMIT:
        return None
    return round(load_per_mille / 10, 1)


def _read_mhz(device_dir: Path | None, attribute: str) -> int | None:
    if device_dir is None:
        return None
    hertz = read_int(device_dir / attribute)
    return None if hertz is None else hertz // HERTZ_PER_MEGAHERTZ
