"""Reports which voice engine models are already present on disk."""

from pathlib import Path

from tools.voice_models.catalog import (
    KOKORO_DIR_NAME,
    KOKORO_VOICES_NAME,
    PIPER_ONNX_NAME,
    QWEN_DIR_NAME,
    QWEN_GGUF_NAME,
    QWEN_MMPROJ_NAME,
)


def check_models(models_dir: Path) -> dict[str, bool]:
    """Checks status of all three neural engine models."""
    piper_file = models_dir / PIPER_ONNX_NAME
    kokoro_dir = models_dir / KOKORO_DIR_NAME
    kokoro_voices = kokoro_dir / KOKORO_VOICES_NAME
    qwen_dir = models_dir / QWEN_DIR_NAME
    qwen_gguf = qwen_dir / QWEN_GGUF_NAME
    qwen_mmproj = qwen_dir / QWEN_MMPROJ_NAME

    return {
        "piper": piper_file.is_file() and piper_file.stat().st_size > 0,
        "kokoro": kokoro_dir.is_dir()
        and kokoro_voices.is_file()
        and kokoro_voices.stat().st_size > 0,
        "qwen": qwen_gguf.is_file()
        and qwen_gguf.stat().st_size > 0
        and qwen_mmproj.is_file()
        and qwen_mmproj.stat().st_size > 0,
    }
