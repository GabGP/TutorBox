#!/usr/bin/env python3
"""Automated Build & Patch Tool for TutorBox Qwen3-TTS Daemon.

Clones pinned upstream llama.cpp (b11002), applies the persistent daemon patch
(0001-llama-tts-daemon-mode.patch), compiles the binary with CUDA or CPU,
and installs llama-tts-daemon into .cache/bin/llama/ alongside its MIT license.

Usage:
    python tools/llama-tts-daemon/build.py
    python tools/llama-tts-daemon/build.py --force
    python tools/llama-tts-daemon/build.py --cpu-only
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

DAEMON_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAEMON_DIR.parent.parent
SOURCE_DIR = ROOT_DIR / ".cache" / "build" / "llama.cpp"
BUILD_DIR = SOURCE_DIR / "build"
PATCH_FILE = DAEMON_DIR / "0001-llama-tts-daemon-mode.patch"
CACHE_BIN_DIR = ROOT_DIR / ".cache" / "bin" / "llama.cpp"
LICENSE_SRC = DAEMON_DIR / "LICENSE-llama-cpp"

PINNED_TAG = "b11002"
UPSTREAM_REPO = "https://github.com/ggerganov/llama.cpp.git"

TAG_OK = "[\033[32mOK\033[0m]"
TAG_INFO = "[\033[34mINFO\033[0m]"
TAG_WARN = "[\033[33mWARN\033[0m]"
TAG_FAIL = "[\033[31mFAIL\033[0m]"


def _find_vcvars64() -> str | None:
    """Finds Visual Studio vcvars64.bat on Windows if MSVC is not yet initialized."""
    if "VCINSTALLDIR" in os.environ:
        return None
    vs_paths = [
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
    for p in vs_paths:
        if p.is_file():
            return str(p)
    return None


def _venv_bin_dirs() -> list[str]:
    """Returns existing venv Scripts/bin dirs so pip-shimmed tools stay on PATH."""
    candidates = [
        Path(sys.prefix) / ("Scripts" if platform.system() == "Windows" else "bin"),
        ROOT_DIR / ".cache" / "venv" / "Scripts",
        ROOT_DIR / ".cache" / "venv" / "bin",
    ]
    seen: set[str] = set()
    dirs: list[str] = []
    for d in candidates:
        # Resolve the dir itself (not a tool path) so cmake/ninja shims are found.
        if d.is_dir():
            resolved = str(d.resolve())
            if resolved not in seen:
                seen.add(resolved)
                dirs.append(resolved)
    return dirs


def _env_with_venv_bins(env: dict[str, str] | None = None) -> dict[str, str]:
    """Merges os.environ with venv bin dirs prepended to PATH.

    pip packages like cmake/ninja install shims into .cache/venv/Scripts,
    which is usually NOT on PATH in a plain shell. Without this, CMake's
    find_program(ninja) fails even though resolve_tool() found the binary.
    """
    merged = dict(os.environ)
    if env:
        merged.update(env)
    path_sep = ";" if platform.system() == "Windows" else ":"
    current = merged.get("PATH", "")
    existing = [p for p in current.split(path_sep) if p]
    existing_lower = (
        {p.lower() for p in existing}
        if platform.system() == "Windows"
        else set(existing)
    )
    prepend: list[str] = []
    for d in _venv_bin_dirs():
        key = d.lower() if platform.system() == "Windows" else d
        if key not in existing_lower:
            prepend.append(d)
            existing_lower.add(key)
    if prepend:
        merged["PATH"] = path_sep.join([*prepend, *existing])
    return merged


def run_cmd(
    cmd: list[str] | str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Executes a subprocess command, wrapping in vcvars64.bat on Windows when needed."""
    is_windows = platform.system() == "Windows"
    vcvars = _find_vcvars64() if is_windows else None
    merged_env = _env_with_venv_bins(env)

    if is_windows and vcvars:
        # list2cmdline quotes args containing spaces (e.g. under Program Files).
        cmd_str = subprocess.list2cmdline(cmd) if isinstance(cmd, list) else cmd
        full_cmd = f'cmd /c "call "{vcvars}" && {cmd_str}"'
        res = subprocess.run(
            full_cmd, cwd=str(cwd or ROOT_DIR), env=merged_env, shell=True, check=False
        )
    else:
        res = subprocess.run(cmd, cwd=str(cwd or ROOT_DIR), env=merged_env, check=False)

    if res.returncode != 0:
        print(f"{TAG_FAIL} Command failed with exit code {res.returncode}: {cmd}")
        sys.exit(res.returncode)


def resolve_tool(name: str) -> str | None:
    """Finds a tool in PATH or inside the active Python virtual environment."""
    found = shutil.which(name)
    if found:
        return found
    ext = ".exe" if platform.system() == "Windows" else ""
    venv_bins = [
        Path(sys.prefix) / "Scripts" / f"{name}{ext}",
        Path(sys.prefix) / "bin" / f"{name}{ext}",
        ROOT_DIR / ".cache" / "venv" / "Scripts" / f"{name}{ext}",
        ROOT_DIR / ".cache" / "venv" / "bin" / f"{name}{ext}",
    ]
    for b in venv_bins:
        if b.is_file():
            return str(b)
    return None


def check_prerequisites() -> bool:
    """Verifies that git and cmake are installed on the host or in virtualenv."""
    if not resolve_tool("git"):
        print(f"{TAG_FAIL} 'git' is not installed or not found in PATH.")
        return False
    if not resolve_tool("cmake"):
        print(f"{TAG_FAIL} 'cmake' is not installed or not found in PATH / virtualenv.")
        return False
    return True


def clone_upstream(force: bool = False) -> None:
    """Clones upstream llama.cpp repository pinned to release b11002."""
    if force and SOURCE_DIR.exists():
        print(
            f"{TAG_INFO} Removing existing build directory for clean rebuild: {SOURCE_DIR}"
        )
        shutil.rmtree(SOURCE_DIR, ignore_errors=True)

    if not (SOURCE_DIR / ".git").is_dir():
        print(f"{TAG_INFO} Cloning {UPSTREAM_REPO} (tag: {PINNED_TAG})...")
        SOURCE_DIR.parent.mkdir(parents=True, exist_ok=True)
        run_cmd(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                PINNED_TAG,
                UPSTREAM_REPO,
                str(SOURCE_DIR),
            ]
        )
    else:
        print(f"{TAG_OK} Upstream repository already present at {SOURCE_DIR}")


def apply_patch(force: bool = False) -> None:
    """Applies the TutorBox daemon line-protocol patch onto upstream llama.cpp."""
    if not PATCH_FILE.is_file():
        print(f"{TAG_FAIL} Patch file not found at {PATCH_FILE}")
        sys.exit(1)

    # Check if patch is already applied
    res = subprocess.run(
        [
            "git",
            "-C",
            str(SOURCE_DIR),
            "apply",
            "--whitespace=nowarn",
            "--reverse",
            "--check",
            str(PATCH_FILE),
        ],
        capture_output=True,
        check=False,
    )
    if res.returncode == 0 and not force:
        print(f"{TAG_OK} Daemon mode patch already cleanly applied.")
        return

    print(f"{TAG_INFO} Applying patch: {PATCH_FILE.name}...")
    run_cmd(
        ["git", "-C", str(SOURCE_DIR), "apply", "--whitespace=nowarn", str(PATCH_FILE)]
    )
    print(f"{TAG_OK} Successfully applied daemon mode patch.")


def build_binary(use_cuda: bool = True, force: bool = False) -> None:
    """Configures CMake and builds target llama-tts."""
    num_jobs = os.cpu_count() or 4
    cmake_bin = resolve_tool("cmake") or "cmake"
    ninja_bin = resolve_tool("ninja")
    has_ninja = bool(ninja_bin)

    if force and BUILD_DIR.exists():
        print(f"{TAG_INFO} Cleaning CMake build directory: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    cmake_cache = BUILD_DIR / "CMakeCache.txt"
    if cmake_cache.is_file():
        cache_content = cmake_cache.read_text(encoding="utf-8", errors="ignore")
        existing_generator = (
            "Ninja" if "CMAKE_GENERATOR:INTERNAL=Ninja" in cache_content else "Other"
        )
        desired_generator = "Ninja" if has_ninja else "Other"
        stale_ninja = (
            "CMAKE_MAKE_PROGRAM:FILEPATH=CMAKE_MAKE_PROGRAM-NOTFOUND" in cache_content
        )
        if existing_generator != desired_generator or (stale_ninja and has_ninja):
            reason = (
                "stale CMAKE_MAKE_PROGRAM-NOTFOUND with ninja now resolvable"
                if stale_ninja and has_ninja and existing_generator == desired_generator
                else f"Generator changed from {existing_generator} to {desired_generator}"
            )
            print(f"{TAG_INFO} {reason}. Cleaning build cache...")
            shutil.rmtree(BUILD_DIR, ignore_errors=True)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    has_cuda = False
    if use_cuda:
        nvcc_bin = shutil.which("nvcc")
        cuda_path = os.environ.get("CUDA_PATH")
        has_cuda = bool(nvcc_bin or cuda_path or Path("/usr/local/cuda").is_dir())
        if has_cuda:
            print(
                f"{TAG_OK} CUDA toolkit detected. Compiling with GPU acceleration (-DGGML_CUDA=ON)..."
            )
        else:
            print(
                f"{TAG_WARN} CUDA compiler not detected in PATH. Falling back to CPU build..."
            )

    cmake_config = [
        cmake_bin,
        "-B",
        str(BUILD_DIR),
        "-S",
        str(SOURCE_DIR),
        "-DGGML_CUDA=ON" if has_cuda else "-DGGML_CUDA=OFF",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DLLAMA_BUILD_TESTS=OFF",
        "-DLLAMA_BUILD_EXAMPLES=OFF",
        "-DLLAMA_BUILD_SERVER=OFF",
    ]
    if has_ninja:
        cmake_config.extend(["-G", "Ninja"])
        # Belt and suspenders: explicit path so CMake never depends on PATH search.
        cmake_config.append(f"-DCMAKE_MAKE_PROGRAM={ninja_bin}")

    print(
        f"{TAG_INFO} Configuring CMake (jobs: {num_jobs}, generator: {'Ninja' if has_ninja else 'default'})..."
    )
    run_cmd(cmake_config, cwd=SOURCE_DIR)

    print(f"{TAG_INFO} Compiling target 'llama-tts' across {num_jobs} threads...")
    cmake_build = [
        cmake_bin,
        "--build",
        str(BUILD_DIR),
        "--target",
        "llama-tts",
        "--config",
        "Release",
        "--parallel",
        str(num_jobs),
    ]
    run_cmd(cmake_build, cwd=SOURCE_DIR)
    print(f"{TAG_OK} Compilation succeeded.")


def install_artifacts() -> None:
    """Installs the compiled binary and MIT license to .cache/bin/llama/."""
    CACHE_BIN_DIR.mkdir(parents=True, exist_ok=True)

    ext = ".exe" if platform.system() == "Windows" else ""
    candidate_bins = [
        BUILD_DIR / "bin" / f"llama-tts{ext}",
        BUILD_DIR / "bin" / "Release" / f"llama-tts{ext}",
        BUILD_DIR / "tools" / "tts" / f"llama-tts{ext}",
        BUILD_DIR / "tools" / "tts" / "Release" / f"llama-tts{ext}",
    ]

    found_bin = next((b for b in candidate_bins if b.is_file()), None)
    if not found_bin:
        print(f"{TAG_FAIL} Compiled binary not found in {BUILD_DIR}")
        sys.exit(1)

    daemon_dest = CACHE_BIN_DIR / f"llama-tts-daemon{ext}"
    license_dest = CACHE_BIN_DIR / "LICENSE-llama-cpp"

    shutil.copy2(found_bin, daemon_dest)
    if not os.access(daemon_dest, os.X_OK) and platform.system() != "Windows":
        os.chmod(daemon_dest, 0o755)

    # Copy all runtime shared libraries (.dll on Windows, .so on Linux, .dylib on macOS)
    bin_dir = found_bin.parent
    lib_patterns = ["*.dll", "*.so*", "*.dylib"]
    for pattern in lib_patterns:
        for lib_file in bin_dir.glob(pattern):
            dest_lib = CACHE_BIN_DIR / lib_file.name
            shutil.copy2(lib_file, dest_lib)
            if not os.access(dest_lib, os.X_OK) and platform.system() != "Windows":
                os.chmod(dest_lib, 0o755)
            print(f"{TAG_OK} Installed library      : {dest_lib}")

    if LICENSE_SRC.is_file():
        shutil.copy2(LICENSE_SRC, license_dest)
    elif (SOURCE_DIR / "LICENSE").is_file():
        shutil.copy2(SOURCE_DIR / "LICENSE", license_dest)

    print(f"{TAG_OK} Installed daemon binary : {daemon_dest}")
    print(f"{TAG_OK} Installed MIT license   : {license_dest}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and install TutorBox llama-tts daemon."
    )
    parser.add_argument(
        "--force", action="store_true", help="Force clean re-clone and re-compilation"
    )
    parser.add_argument(
        "--cpu-only", action="store_true", help="Disable CUDA GPU offloading"
    )
    args = parser.parse_args()

    print("==================================================")
    print("      TutorBox Qwen3-TTS Daemon Build Tool        ")
    print("==================================================")

    if not check_prerequisites():
        sys.exit(1)

    clone_upstream(force=args.force)
    apply_patch(force=args.force)
    build_binary(use_cuda=not args.cpu_only, force=args.force)
    install_artifacts()

    print("--------------------------------------------------")
    print(
        f"{TAG_OK} Build complete! Qwen3-TTS daemon is ready for appliance deployment."
    )
    print("==================================================")


if __name__ == "__main__":
    main()
