"""Per-engine download steps: Piper/Sherpa, Kokoro-82M and Qwen3-TTS."""

import tarfile
from pathlib import Path

from tools.voice_models.archive import safe_extract_tar
from tools.voice_models.catalog import (
    KOKORO_ARCHIVE_NAME,
    KOKORO_DIR_NAME,
    KOKORO_INT8_MODEL_NAME,
    KOKORO_MODEL_NAME,
    KOKORO_TAR_URL,
    KOKORO_VOICES_NAME,
    PIPER_BASE_URL,
    PIPER_CONFIG_NAME,
    PIPER_ONNX_NAME,
    PIPER_SHERPA_NAME,
    PIPER_TOKENS_NAME,
    QWEN_BASE_URL,
    QWEN_DIR_NAME,
    QWEN_GGUF_NAME,
    QWEN_MMPROJ_NAME,
)
from tools.voice_models.console import TAG_FAIL, TAG_INFO, TAG_OK
from tools.voice_models.sherpa import generate_sherpa_model, generate_sherpa_tokens
from tools.voice_models.transfer import download_file


def download_piper(models_dir: Path, force: bool = False) -> bool:
    """Downloads Piper / Sherpa Spanish Harvard ONNX model and config."""
    onnx_file = models_dir / PIPER_ONNX_NAME
    json_file = models_dir / PIPER_CONFIG_NAME
    tokens_file = models_dir / PIPER_TOKENS_NAME
    sherpa_file = models_dir / PIPER_SHERPA_NAME

    onnx_ok = download_file(
        f"{PIPER_BASE_URL}/{PIPER_ONNX_NAME}",
        onnx_file,
        label="Spanish Harvard ONNX model (~76 MB)",
        force=force,
    )
    json_ok = download_file(
        f"{PIPER_BASE_URL}/{PIPER_CONFIG_NAME}",
        json_file,
        label="Spanish Harvard ONNX config (~5 KB)",
        force=force,
    )

    if json_ok and onnx_ok:
        generate_sherpa_tokens(json_file, tokens_file)
        generate_sherpa_model(onnx_file, json_file, sherpa_file, force=force)

    return onnx_ok and json_ok


def download_kokoro(models_dir: Path, force: bool = False) -> bool:
    """Downloads and extracts Kokoro-82M multilingual INT8 ONNX bundle."""
    kokoro_dir = models_dir / KOKORO_DIR_NAME
    voices_file = kokoro_dir / KOKORO_VOICES_NAME
    model_file = kokoro_dir / KOKORO_MODEL_NAME
    int8_model_file = kokoro_dir / KOKORO_INT8_MODEL_NAME

    if (
        kokoro_dir.is_dir()
        and voices_file.is_file()
        and (model_file.is_file() or int8_model_file.is_file())
        and not force
    ):
        print(f"{TAG_OK} Already present: Kokoro-82M bundle ({kokoro_dir.name})")
        return True

    tar_path = models_dir / KOKORO_ARCHIVE_NAME
    archive_ok = download_file(
        KOKORO_TAR_URL,
        tar_path,
        label="Kokoro-82M INT8 archive (~140 MB)",
        force=force,
    )
    if not archive_ok:
        return False

    print(f"{TAG_INFO} Extracting Kokoro-82M archive...")
    try:
        safe_extract_tar(tar_path, models_dir)
        tar_path.unlink(missing_ok=True)
        print(f"{TAG_OK} Extracted Kokoro-82M model to {kokoro_dir.name}")
        return True
    except (OSError, tarfile.TarError) as err:
        print(f"{TAG_FAIL} Extraction failed: {err}")
        return False


def download_qwen(models_dir: Path, force: bool = False) -> bool:
    """Downloads Qwen3-TTS 1.7B Base GGUF weights and multimodal projector."""
    qwen_dir = models_dir / QWEN_DIR_NAME
    gguf_file = qwen_dir / QWEN_GGUF_NAME
    mmproj_file = qwen_dir / QWEN_MMPROJ_NAME

    gguf_ok = download_file(
        f"{QWEN_BASE_URL}/{QWEN_GGUF_NAME}",
        gguf_file,
        label="Qwen3-TTS Base Q4_K_M GGUF (~1.03 GB)",
        force=force,
    )
    mmproj_ok = download_file(
        f"{QWEN_BASE_URL}/{QWEN_MMPROJ_NAME}",
        mmproj_file,
        label="Qwen3-TTS mmproj Q8_0 GGUF (~446 MB)",
        force=force,
    )

    return gguf_ok and mmproj_ok
