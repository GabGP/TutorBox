"""Configures CMake and compiles the llama-tts target, with CUDA when a toolkit exists."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.cmake_cache import discard_stale_cache
from tools.llama_tts_daemon.build_llama.commands import run_cmd
from tools.llama_tts_daemon.build_llama.console import TAG_INFO, TAG_OK, TAG_WARN
from tools.llama_tts_daemon.build_llama.toolchain import resolve_tool

BUILD_TARGET = "llama-tts"
DEFAULT_JOB_COUNT = 4
UNIX_CUDA_TOOLKIT_DIR = Path("/usr/local/cuda")


def detect_cuda(use_cuda: bool) -> bool:
    """Reports whether a CUDA toolkit is available, announcing the chosen backend."""
    if not use_cuda:
        return False
    nvcc_bin = shutil.which("nvcc")
    cuda_path = os.environ.get("CUDA_PATH")
    has_cuda = bool(nvcc_bin or cuda_path or UNIX_CUDA_TOOLKIT_DIR.is_dir())
    if has_cuda:
        print(
            f"{TAG_OK} CUDA toolkit detected. Compiling with GPU acceleration (-DGGML_CUDA=ON)..."
        )
    else:
        print(
            f"{TAG_WARN} CUDA compiler not detected in PATH. Falling back to CPU build..."
        )
    return has_cuda


def _configure_command(
    cmake_bin: str, ninja_bin: str | None, has_cuda: bool
) -> list[str]:
    """Builds the CMake configure command for the daemon target."""
    cmake_config = [
        cmake_bin,
        "-B",
        str(paths.BUILD_DIR),
        "-S",
        str(paths.SOURCE_DIR),
        "-DGGML_CUDA=ON" if has_cuda else "-DGGML_CUDA=OFF",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DLLAMA_BUILD_TESTS=OFF",
        "-DLLAMA_BUILD_EXAMPLES=OFF",
        "-DLLAMA_BUILD_SERVER=OFF",
    ]
    if ninja_bin:
        cmake_config.extend(["-G", "Ninja"])
        # Belt and suspenders: explicit path so CMake never depends on PATH search.
        cmake_config.append(f"-DCMAKE_MAKE_PROGRAM={ninja_bin}")
    return cmake_config


def _build_command(cmake_bin: str, num_jobs: int) -> list[str]:
    """Builds the CMake build command for the llama-tts target."""
    return [
        cmake_bin,
        "--build",
        str(paths.BUILD_DIR),
        "--target",
        BUILD_TARGET,
        "--config",
        "Release",
        "--parallel",
        str(num_jobs),
    ]


def build_binary(use_cuda: bool = True, force: bool = False) -> None:
    """Configures CMake and builds target llama-tts."""
    num_jobs = os.cpu_count() or DEFAULT_JOB_COUNT
    cmake_bin = resolve_tool("cmake") or "cmake"
    ninja_bin = resolve_tool("ninja")
    has_ninja = bool(ninja_bin)

    if force and paths.BUILD_DIR.exists():
        print(f"{TAG_INFO} Cleaning CMake build directory: {paths.BUILD_DIR}")
        shutil.rmtree(paths.BUILD_DIR, ignore_errors=True)

    discard_stale_cache(has_ninja)

    paths.BUILD_DIR.mkdir(parents=True, exist_ok=True)

    has_cuda = detect_cuda(use_cuda)

    generator_label = "Ninja" if has_ninja else "default"
    print(
        f"{TAG_INFO} Configuring CMake (jobs: {num_jobs}, generator: {generator_label})..."
    )
    run_cmd(_configure_command(cmake_bin, ninja_bin, has_cuda), cwd=paths.SOURCE_DIR)

    print(f"{TAG_INFO} Compiling target '{BUILD_TARGET}' across {num_jobs} threads...")
    run_cmd(_build_command(cmake_bin, num_jobs), cwd=paths.SOURCE_DIR)
    print(f"{TAG_OK} Compilation succeeded.")
