"""Turns a reading into the status the panel colours it with: ok, warn, critical or unknown."""

from core.system_health import thresholds
from core.system_health.models import HealthStatus

__all__ = [
    "cpu_status",
    "disk_status",
    "gpu_status",
    "memory_status",
    "temperature_status",
]


def temperature_status(celsius: float | None) -> HealthStatus:
    """Warns from the warn temperature up, and turns critical from the critical one up."""
    return _status_when_at_least(
        celsius,
        thresholds.TEMPERATURE_WARN_CELSIUS,
        thresholds.TEMPERATURE_CRITICAL_CELSIUS,
    )


def cpu_status(usage_percent: float | None) -> HealthStatus:
    """Warns when the CPU is busy; the CPU has no critical limit of its own."""
    return _status_when_at_least(usage_percent, thresholds.CPU_USAGE_WARN_PERCENT, None)


def gpu_status(load_percent: float | None) -> HealthStatus:
    """Informational: a busy GPU is the normal state during generation, so it never warns."""
    return "unknown" if load_percent is None else "ok"


def memory_status(available_mb: float | None) -> HealthStatus:
    """Warns when little memory is left for the models, and turns critical when almost none is."""
    return _status_when_below(
        available_mb,
        thresholds.MEMORY_AVAILABLE_WARN_MB,
        thresholds.MEMORY_AVAILABLE_CRITICAL_MB,
    )


def disk_status(free_percent: float | None) -> HealthStatus:
    """Warns when the database partition runs low on free space, and turns critical when it is nearly full."""
    return _status_when_below(
        free_percent,
        thresholds.DISK_FREE_WARN_PERCENT,
        thresholds.DISK_FREE_CRITICAL_PERCENT,
    )


def _status_when_at_least(
    value: float | None, warn_at: float, critical_at: float | None
) -> HealthStatus:
    if value is None:
        return "unknown"
    if critical_at is not None and value >= critical_at:
        return "critical"
    if value >= warn_at:
        return "warn"
    return "ok"


def _status_when_below(
    value: float | None, warn_below: float, critical_below: float
) -> HealthStatus:
    if value is None:
        return "unknown"
    if value < critical_below:
        return "critical"
    if value < warn_below:
        return "warn"
    return "ok"
