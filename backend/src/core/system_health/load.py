"""Uptime and the load average, from /proc/uptime and /proc/loadavg."""

from pathlib import Path

from core.system_health.files import HOST_ROOT, read_text

__all__ = ["read_load_average", "read_uptime_seconds"]

LOAD_AVERAGE_FIELDS = 3


def read_uptime_seconds(root: Path = HOST_ROOT) -> float | None:
    """Seconds since boot, or None when /proc/uptime does not hold a number."""
    fields = (read_text(root / "proc" / "uptime") or "").split()
    return _parse_float(fields[0]) if fields else None


def read_load_average(root: Path = HOST_ROOT) -> list[float] | None:
    """The 1, 5 and 15 minute load averages, or None unless all three are numbers."""
    text = read_text(root / "proc" / "loadavg")
    if text is None:
        return None
    parsed = [_parse_float(field) for field in text.split()[:LOAD_AVERAGE_FIELDS]]
    if len(parsed) < LOAD_AVERAGE_FIELDS or None in parsed:
        return None
    return [round(value, 2) for value in parsed if value is not None]


def _parse_float(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None
