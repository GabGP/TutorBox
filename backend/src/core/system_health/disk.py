"""Free space on the partition that holds the database."""

import shutil
from pathlib import Path

from core.system_health.models import DiskReading
from core.system_health.status import disk_status

__all__ = ["read_disk"]

BYTES_PER_GIBIBYTE = 1024**3


def read_disk(directory: Path) -> DiskReading | None:
    """Size and free space of the partition under `directory`; None when it cannot be read."""
    try:
        usage = shutil.disk_usage(directory)
    except OSError:
        return None
    if usage.total <= 0:
        return None
    free_percent = round(100 * usage.free / usage.total, 1)
    return DiskReading(
        total_gb=round(usage.total / BYTES_PER_GIBIBYTE, 1),
        free_gb=round(usage.free / BYTES_PER_GIBIBYTE, 1),
        free_percent=free_percent,
        status=disk_status(free_percent),
    )
