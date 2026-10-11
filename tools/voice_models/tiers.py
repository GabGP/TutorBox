"""Maps a requested download tier onto the voice engines it includes."""

from pathlib import Path

from tools.voice_models.catalog import DEFAULT_MODELS_DIR
from tools.voice_models.engines import download_kokoro, download_piper, download_qwen

TARGET_CHOICES = ["minimal", "piper", "kokoro", "qwen", "all"]
DEFAULT_TARGET = "minimal"


def execute_download(
    target: str = DEFAULT_TARGET,
    models_dir: Path | None = None,
    force: bool = False,
) -> bool:
    """Coordinates download based on requested target tier."""
    effective_dir = models_dir or DEFAULT_MODELS_DIR
    effective_dir.mkdir(parents=True, exist_ok=True)

    success = True
    if target in ("minimal", "piper", "all"):
        success = download_piper(effective_dir, force=force) and success
    if target in ("kokoro", "all"):
        success = download_kokoro(effective_dir, force=force) and success
    if target in ("qwen", "all"):
        success = download_qwen(effective_dir, force=force) and success

    return success
