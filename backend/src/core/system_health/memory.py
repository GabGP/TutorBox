"""RAM and swap from /proc/meminfo."""

from pathlib import Path

from core.system_health.files import HOST_ROOT, read_text
from core.system_health.models import MemoryReading
from core.system_health.status import memory_status

__all__ = ["read_memory"]

KIBIBYTES_PER_MEBIBYTE = 1024


def read_memory(root: Path = HOST_ROOT) -> MemoryReading | None:
    """Total and available RAM, and swap. None unless MemTotal and MemAvailable are readable."""
    meminfo_text = read_text(root / "proc" / "meminfo")
    if meminfo_text is None:
        return None
    values_kib = _parse_meminfo(meminfo_text)
    total_kib = values_kib.get("MemTotal")
    available_kib = values_kib.get("MemAvailable")
    if not total_kib or available_kib is None:
        return None
    available_mb = _to_mebibytes(available_kib)
    swap_total_kib = values_kib.get("SwapTotal", 0)
    swap_free_kib = values_kib.get("SwapFree", 0)
    return MemoryReading(
        total_mb=_to_mebibytes(total_kib),
        available_mb=available_mb,
        used_percent=round(100 * (total_kib - available_kib) / total_kib, 1),
        swap_total_mb=_to_mebibytes(swap_total_kib),
        swap_used_mb=_to_mebibytes(max(0, swap_total_kib - swap_free_kib)),
        status=memory_status(available_mb),
    )


def _parse_meminfo(text: str) -> dict[str, int]:
    """Maps each `Key: value kB` line to its value in KiB; lines that do not parse are skipped."""
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, separator, rest = line.partition(":")
        fields = rest.split()
        if separator and fields and fields[0].isdigit():
            values[key.strip()] = int(fields[0])
    return values


def _to_mebibytes(kibibytes: int) -> float:
    return round(kibibytes / KIBIBYTES_PER_MEBIBYTE, 1)
