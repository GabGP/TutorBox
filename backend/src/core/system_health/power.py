"""Power drawn through the INA3221 monitor: each VDD_ rail, from its voltage and current."""

from pathlib import Path

from core.system_health.files import HOST_ROOT, in_numeric_order, read_int, read_text
from core.system_health.models import PowerReading

__all__ = ["read_power_rails"]

# One hwmon node per monitor chip, whatever its I2C address is.
INA3221_HWMON_PATTERN = "sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*"
RAIL_LABEL_PREFIX = "VDD_"
MILLIVOLT_MILLIAMP_PER_MILLIWATT = 1000


def read_power_rails(root: Path = HOST_ROOT) -> list[PowerReading]:
    """Every labelled VDD_ rail with both its voltage and its current; empty when none is readable."""
    readings: list[PowerReading] = []
    for hwmon_dir in in_numeric_order(root.glob(INA3221_HWMON_PATTERN)):
        readings.extend(_rails_of(hwmon_dir))
    return readings


def _rails_of(hwmon_dir: Path) -> list[PowerReading]:
    rails: list[PowerReading] = []
    for label_file in in_numeric_order(hwmon_dir.glob("in*_label")):
        channel = label_file.name.removeprefix("in").removesuffix("_label")
        if not channel.isdigit():
            continue
        label = (read_text(label_file) or "").strip()
        if not label.startswith(RAIL_LABEL_PREFIX):
            continue
        milliwatts = _milliwatts(hwmon_dir, channel)
        if milliwatts is not None:
            rails.append(PowerReading(rail=label, milliwatts=milliwatts))
    return rails


def _milliwatts(hwmon_dir: Path, channel: str) -> int | None:
    millivolts = read_int(hwmon_dir / f"in{channel}_input")
    milliamps = read_int(hwmon_dir / f"curr{channel}_input")
    if millivolts is None or milliamps is None:
        return None
    return round(millivolts * milliamps / MILLIVOLT_MILLIAMP_PER_MILLIWATT)
