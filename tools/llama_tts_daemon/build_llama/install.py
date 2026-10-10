"""Installs the compiled llama-tts daemon binary, runtime libraries and MIT license."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL, TAG_OK

LLAMA_TTS_BINARY_NAME = "llama-tts"
DAEMON_BINARY_NAME = "llama-tts-daemon"
INSTALLED_LICENSE_NAME = "LICENSE-llama-cpp"
RUNTIME_LIBRARY_PATTERNS = ["*.dll", "*.so*", "*.dylib"]
EXECUTABLE_PERMISSIONS = 0o755


def _executable_extension() -> str:
    """Returns ".exe" on Windows and an empty string elsewhere."""
    return ".exe" if platform.system() == "Windows" else ""


def find_built_binary() -> Path | None:
    """Returns the compiled llama-tts binary from the first build folder that has it."""
    ext = _executable_extension()
    binary_name = f"{LLAMA_TTS_BINARY_NAME}{ext}"
    # The four folders CMake may place the target in, searched in this order.
    candidate_bins = [
        paths.BUILD_DIR / "bin" / binary_name,
        paths.BUILD_DIR / "bin" / "Release" / binary_name,
        paths.BUILD_DIR / "tools" / "tts" / binary_name,
        paths.BUILD_DIR / "tools" / "tts" / "Release" / binary_name,
    ]
    return next(
        (
            candidate_path
            for candidate_path in candidate_bins
            if candidate_path.is_file()
        ),
        None,
    )


def _ensure_executable(installed_path: Path) -> None:
    """Marks an installed file executable on platforms that use permission bits."""
    if not os.access(installed_path, os.X_OK) and platform.system() != "Windows":
        os.chmod(installed_path, EXECUTABLE_PERMISSIONS)


def install_runtime_libraries(bin_dir: Path) -> None:
    """Copies the shared libraries next to the binary into the install folder."""
    # Copy all runtime shared libraries (.dll on Windows, .so on Linux, .dylib on macOS)
    for pattern in RUNTIME_LIBRARY_PATTERNS:
        for lib_file in bin_dir.glob(pattern):
            dest_lib = paths.CACHE_BIN_DIR / lib_file.name
            shutil.copy2(lib_file, dest_lib)
            _ensure_executable(dest_lib)
            print(f"{TAG_OK} Installed library      : {dest_lib}")


def _install_license(license_dest: Path) -> None:
    """Copies the bundled MIT license, falling back to the upstream LICENSE file."""
    if paths.LICENSE_SRC.is_file():
        shutil.copy2(paths.LICENSE_SRC, license_dest)
    elif (paths.SOURCE_DIR / "LICENSE").is_file():
        shutil.copy2(paths.SOURCE_DIR / "LICENSE", license_dest)


def install_artifacts() -> None:
    """Installs the compiled binary and MIT license to .cache/bin/llama.cpp/."""
    paths.CACHE_BIN_DIR.mkdir(parents=True, exist_ok=True)

    ext = _executable_extension()
    found_bin = find_built_binary()
    if not found_bin:
        print(f"{TAG_FAIL} Compiled binary not found in {paths.BUILD_DIR}")
        sys.exit(1)

    daemon_dest = paths.CACHE_BIN_DIR / f"{DAEMON_BINARY_NAME}{ext}"
    license_dest = paths.CACHE_BIN_DIR / INSTALLED_LICENSE_NAME

    shutil.copy2(found_bin, daemon_dest)
    _ensure_executable(daemon_dest)

    install_runtime_libraries(found_bin.parent)
    _install_license(license_dest)

    print(f"{TAG_OK} Installed daemon binary : {daemon_dest}")
    print(f"{TAG_OK} Installed MIT license   : {license_dest}")
