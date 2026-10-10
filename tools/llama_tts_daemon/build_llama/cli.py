"""Command-line flags and step order of the llama-tts daemon build."""

import argparse
import sys

from tools.llama_tts_daemon.build_llama.compile import build_binary
from tools.llama_tts_daemon.build_llama.console import (
    BANNER_LINE,
    SEPARATOR_LINE,
    TAG_OK,
)
from tools.llama_tts_daemon.build_llama.install import install_artifacts
from tools.llama_tts_daemon.build_llama.source import apply_patch, clone_upstream
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
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint for the Utz'tutor llama-tts daemon build."""
    args = parse_arguments()

    print(BANNER_LINE)
    print("      Utz'tutor Qwen3-TTS Daemon Build Tool        ")
    print(BANNER_LINE)

    if not check_prerequisites():
        sys.exit(1)

    clone_upstream(force=args.force)
    apply_patch(force=args.force)
    build_binary(use_cuda=not args.cpu_only, force=args.force)
    install_artifacts()

    print(SEPARATOR_LINE)
    print(
        f"{TAG_OK} Build complete! Qwen3-TTS daemon is ready for appliance deployment."
    )
    print(BANNER_LINE)
