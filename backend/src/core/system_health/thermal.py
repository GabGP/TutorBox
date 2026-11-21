"""The SoC's thermal zones. Zones that read nothing or an impossible value are left out."""

from pathlib import Path

from core.system_health.files import HOST_ROOT, in_numeric_order, read_int, read_text
from core.system_health.models import TemperatureReading
from core.system_health.status import temperature_status

__all__ = ["read_temperatures"]

THERMAL_ZONE_PATTERN = "sys/devices/virtual/thermal/thermal_zone*"
MILLIDEGREES_PER_DEGREE = 1000
# Some cv zones report -256000 (-256 °C) or nothing. No real SoC sensor reads outside this.
PLAUSIBLE_MIN_CELSIUS = -40.0
PLAUSIBLE_MAX_CELSIUS = 150.0


def read_temperatures(root: Path = HOST_ROOT) -> list[TemperatureReading]:
    """Every zone with a plausible reading, in zone order, named by the zone's type."""
    readings: list[TemperatureReading] = []
    for zone_dir in in_numeric_order(root.glob(THERMAL_ZONE_PATTERN)):
        celsius = _read_celsius(zone_dir)
        if celsius is None:
            continue
        readings.append(
            TemperatureReading(
                zone=_zone_name(zone_dir),
                celsius=celsius,
                status=temperature_status(celsius),
            )
        )
    return readings


def _read_celsius(zone_dir: Path) -> float | None:
    millidegrees = read_int(zone_dir / "temp")
    if millidegrees is None:
        return None
    celsius = millidegrees / MILLIDEGREES_PER_DEGREE
    if not PLAUSIBLE_MIN_CELSIUS <= celsius <= PLAUSIBLE_MAX_CELSIUS:
        return None
    return round(celsius, 1)


def _zone_name(zone_dir: Path) -> str:
    zone_type = read_text(zone_dir / "type")
    if zone_type is None or not zone_type.strip():
        return zone_dir.name
    return zone_type.strip()
