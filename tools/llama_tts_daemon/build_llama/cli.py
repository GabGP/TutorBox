"""Command-line flags and step order of the llama-tts daemon build."""

import argparse
import sys

from tools.llama_tts_daemon.build_llama.compile import build_binary, has_cuda_toolkit
from tools.llama_tts_daemon.build_llama.console import (
    BANNER_LINE,
    SEPARATOR_LINE,
    TAG_FAIL,
    TAG_OK,
)
from tools.llama_tts_daemon.build_llama.install import install_artifacts
from tools.llama_tts_daemon.build_llama.source import apply_patches, clone_upstream
from tools.llama_tts_daemon.build_llama.toolchain import check_prerequisites


def parse_arguments() -> argparse.Namespace:
    """Parses the build.py command-line flags."""
    parser = argparse.ArgumentParser(
        description="Build and install Utz'tutor llama-tts daemon."
    )
    parser.add_argument(
        "--force", action="store_true", help="Force clean re-clone and re-compilation"
    )
    parser.add_argument(
        "--cpu-only", action="store_true", help="Disable CUDA GPU offloading"
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Fail instead of building for CPU when no CUDA toolkit is found",
    )
    arguments = parser.parse_args()
    if arguments.cpu_only and arguments.require_cuda:
        parser.error("--cpu-only and --require-cuda cannot be used together")
    return arguments


def main() -> None:
    """CLI entrypoint for the Utz'tutor llama-tts daemon build."""
    args = parse_arguments()

    print(BANNER_LINE)
    print("      Utz'tutor Qwen3-TTS Daemon Build Tool        ")
    print(BANNER_LINE)

    if not check_prerequisites():
        sys.exit(1)
    if args.require_cuda and not has_cuda_toolkit():
        print(
            f"{TAG_FAIL} --require-cuda: no CUDA toolkit found (nvcc on PATH, CUDA_PATH or /usr/local/cuda)."
        )
        sys.exit(1)

    clone_upstream(force=args.force)
    apply_patches(force=args.force)
    build_binary(use_cuda=not args.cpu_only, force=args.force)
    install_artifacts()

    print(SEPARATOR_LINE)
    print(
        f"{TAG_OK} Build complete! Qwen3-TTS daemon is ready for appliance deployment."
    )
    print(BANNER_LINE)
