"""NVIDIA Jetson detection from the Tegra release file or the aarch64 SoC family."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

TEGRA_RELEASE_FILE = Path("/etc/nv_tegra_release")
SOC_FAMILY_FILE = Path("/sys/devices/soc0/family")


def is_jetson_uma() -> bool:
    """Returns True if the runtime platform is an NVIDIA Jetson (Tegra UMA)."""
    if TEGRA_RELEASE_FILE.exists():
        return True
    if sys.platform.startswith("linux") and platform.machine() == "aarch64":
        if (
            SOC_FAMILY_FILE.exists()
            and "tegra" in SOC_FAMILY_FILE.read_text(encoding="utf-8").lower()
        ):
            return True
    return False
