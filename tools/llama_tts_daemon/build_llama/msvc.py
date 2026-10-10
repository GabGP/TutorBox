"""Locates the Visual Studio vcvars64.bat script used to initialize MSVC."""

from __future__ import annotations

import os
from pathlib import Path

VCVARS64_CANDIDATES: list[Path] = [
    Path(
        "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"
    ),
    Path(
        "C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvars64.bat"
    ),
    Path(
        "C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvars64.bat"
    ),
    Path(
        "C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"
    ),
    Path(
        "C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Auxiliary/Build/vcvars64.bat"
    ),
    Path(
        "C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvars64.bat"
    ),
]


def find_vcvars64() -> str | None:
    """Finds Visual Studio vcvars64.bat on Windows if MSVC is not yet initialized."""
    if "VCINSTALLDIR" in os.environ:
        return None
    for candidate_path in VCVARS64_CANDIDATES:
        if candidate_path.is_file():
            return str(candidate_path)
    return None
