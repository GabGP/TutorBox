"""Model path resolution and configuration sanitization for Piper-TTS."""

import json
import logging
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.exceptions import TTSUnavailableError

__all__ = ["resolve_model_path", "sanitize_model_config"]

logger = logging.getLogger(__name__)


def resolve_model_path(model_name: str, custom_dir: str = "") -> Path:
    """Finds the ONNX model file across configured and standard search paths."""
    candidates = [
        Path(custom_dir) if custom_dir else None,
        Path(get_settings().tts.piper_model_dir),
        PROJECT_ROOT / ".cache" / "models" / "tts",
        Path.cwd() / "models" / "tts",
    ]
    for directory in filter(None, candidates):
        model_file = directory / model_name
        if model_file.is_file():
            return model_file.resolve()
    raise TTSUnavailableError(f"Piper model '{model_name}' was not found.")


def sanitize_model_config(config_path: Path) -> None:
    """Normalizes legacy enum literals in model JSON configurations."""
    if not config_path.is_file():
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("phoneme_type") == "PhonemeType.ESPEAK":
            data["phoneme_type"] = "espeak"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    except (OSError, json.JSONDecodeError) as err:
        logger.warning("Could not sanitize Piper config %s: %s", config_path, err)
