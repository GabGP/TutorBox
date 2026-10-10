"""Command-line flags, diagnostic report and step order of the voice model downloader."""

import argparse
import sys
from pathlib import Path

from tools.voice_models.catalog import DEFAULT_MODELS_DIR
from tools.voice_models.console import (
    BANNER_LINE,
    SEPARATOR_LINE,
    TAG_FAIL,
    TAG_OK,
    TAG_WARN,
)
from tools.voice_models.status import check_models
from tools.voice_models.tiers import DEFAULT_TARGET, TARGET_CHOICES, execute_download


def parse_arguments() -> argparse.Namespace:
    """Parses the download_models.py command-line flags."""
    parser = argparse.ArgumentParser(
        description="Download offline voice models for Utz'tutor"
    )
    parser.add_argument(
        "--target",
        choices=TARGET_CHOICES,
        default=DEFAULT_TARGET,
        help="Target voice engine models to download (default: minimal)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="Destination directory for models (default: .cache/models/tts)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download of existing models",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check presence of models and exit without downloading",
    )
    return parser.parse_args()


def print_diagnostic(status: dict[str, bool]) -> None:
    """Prints which voice engine models are present and which are missing."""
    print(BANNER_LINE)
    print("         Utz'tutor TTS Models Diagnostic           ")
    print(BANNER_LINE)
    print(
        f"  * Piper / Sherpa (Spanish) : "
        f"{TAG_OK if status['piper'] else TAG_WARN + ' Missing'}"
    )
    print(
        f"  * Kokoro-82M (Multilingual): "
        f"{TAG_OK if status['kokoro'] else TAG_WARN + ' Missing'}"
    )
    print(
        f"  * Qwen3-TTS (GGUF Weights) : "
        f"{TAG_OK if status['qwen'] else TAG_WARN + ' Missing'}"
    )
    print(SEPARATOR_LINE)


def main() -> None:
    """CLI entrypoint for Utz'tutor model downloader."""
    args = parse_arguments()

    status = check_models(args.models_dir)
    print_diagnostic(status)

    if args.check_only:
        missing_count = sum(1 for present in status.values() if not present)
        sys.exit(1 if missing_count > 0 else 0)

    print(f"Downloading target tier: '{args.target}'...")
    success = execute_download(
        target=args.target,
        models_dir=args.models_dir,
        force=args.force,
    )
    print(SEPARATOR_LINE)
    if success:
        print(f"{TAG_OK} Voice model setup complete.")
    else:
        print(f"{TAG_FAIL} One or more model downloads failed.")
        sys.exit(1)
