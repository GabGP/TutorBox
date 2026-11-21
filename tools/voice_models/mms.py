"""Download step for the Meta MMS-TTS Kʼicheʼ and Qʼeqchiʼ checkpoints.

Each checkpoint serves the downloads-page generator (transformers) and, once
exported to model.onnx, the classroom voice engine (ONNX Runtime).
"""

from pathlib import Path

from tools.voice_models.catalog import (
    MMS_BASE_URL,
    MMS_DIR_NAME,
    MMS_FILE_NAMES,
    MMS_MODELS,
    MMS_ONNX_NAME,
    MMS_WEIGHTS_NAME,
)
from tools.voice_models.mms_onnx import export_mms_onnx
from tools.voice_models.transfer import download_file


def mms_model_dir(models_dir: Path, model_name: str) -> Path:
    """Folder that holds one MMS checkpoint, loadable by transformers offline."""
    return models_dir / MMS_DIR_NAME / model_name


def download_mms(models_dir: Path, force: bool = False) -> bool:
    """Downloads and exports both MMS checkpoints; keeps going after a failure."""
    success = True
    for model_name in MMS_MODELS:
        target_dir = mms_model_dir(models_dir, model_name)
        model_ok = True
        for file_name in MMS_FILE_NAMES:
            size_hint = " (~145 MB)" if file_name == MMS_WEIGHTS_NAME else ""
            file_ok = download_file(
                f"{MMS_BASE_URL}/{model_name}/resolve/main/{file_name}",
                target_dir / file_name,
                label=f"MMS {model_name} {file_name}{size_hint}",
                force=force,
            )
            model_ok = file_ok and model_ok
        if model_ok:
            model_ok = export_mms_onnx(target_dir, force=force)
        success = model_ok and success
    return success


def mms_models_present(models_dir: Path) -> bool:
    """True when both checkpoints and their ONNX exports are on disk, none empty."""
    for model_name in MMS_MODELS:
        target_dir = mms_model_dir(models_dir, model_name)
        for file_name in (*MMS_FILE_NAMES, MMS_ONNX_NAME):
            model_file = target_dir / file_name
            if not (model_file.is_file() and model_file.stat().st_size > 0):
                return False
    return True
