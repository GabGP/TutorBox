"""Command-line flags accepted by the Utz'tutor launcher."""

import argparse


def parse_arguments() -> argparse.Namespace:
    """Parses the run.py command-line flags."""
    parser = argparse.ArgumentParser(
        description="Utz'tutor Appliance Dev & Production Launcher"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--no-reload", action="store_true", help="Disable auto-reloading"
    )
    parser.add_argument(
        "--no-build", action="store_true", help="Skip frontend PWA compilation"
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Skip backend dependency synchronization (uv sync --all-extras)",
    )
    parser.add_argument(
        "--build-llama",
        action="store_true",
        help="Compile and install patched llama-tts daemon before launching",
    )
    parser.add_argument(
        "--force-build-llama",
        action="store_true",
        help="Force clean re-clone and recompilation of llama-tts daemon",
    )
    parser.add_argument(
        "--download-models",
        nargs="?",
        const="minimal",
        choices=["minimal", "kokoro", "qwen", "all"],
        help="Download voice models before launching (choices: minimal, kokoro, qwen, all; default: minimal)",
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Check prerequisites and exit"
    )
    return parser.parse_args()
