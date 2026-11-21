"""Where the Mayan MMS voices live on disk and how one is loaded.

tools/voice_models downloads each checkpoint into <models>/mms/<name>/ and
exports model.onnx next to its vocab.json and config.json. ONNX Runtime (a
piper-tts dependency) runs it, so the backend never imports PyTorch.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import PROJECT_ROOT, get_settings
from core.tts.exceptions import TTSUnavailableError

__all__ = [
    "MMS_CHECKPOINTS",
    "MMS_ONNX_NAME",
    "MmsVoice",
    "find_mms_dir",
    "load_mms_voice",
]

# Language code -> Meta MMS-TTS checkpoint (Hugging Face facebook/<name>).
MMS_CHECKPOINTS: dict[str, str] = {
    "quc": "mms-tts-quc-dialect_central",
    "kek": "mms-tts-kek",
}
MMS_ONNX_NAME = "model.onnx"
_VOCABULARY_NAME = "vocab.json"
_CONFIG_NAME = "config.json"
_DEFAULT_SAMPLE_RATE_HZ = 16000


@dataclass(frozen=True)
class MmsVoice:
    """One loaded MMS voice: its ONNX session, alphabet and output rate."""

    session: Any
    vocabulary: dict[str, int]
    sample_rate: int


def find_mms_dir(lang: str) -> Path | None:
    """Folder holding the language's exported voice, or None when missing."""
    checkpoint = MMS_CHECKPOINTS.get(lang)
    if checkpoint is None:
        return None
    tts = get_settings().tts
    candidate_dirs = (
        Path(tts.mms_model_dir) / checkpoint,
        PROJECT_ROOT / ".cache" / "models" / "tts" / tts.mms_model_dir / checkpoint,
        Path(tts.piper_model_dir) / tts.mms_model_dir / checkpoint,
    )
    return next(
        (
            directory.resolve()
            for directory in candidate_dirs
            if (directory / MMS_ONNX_NAME).is_file()
            and (directory / _VOCABULARY_NAME).is_file()
        ),
        None,
    )


def load_mms_voice(lang: str) -> MmsVoice:
    """Opens the language's ONNX voice on the CPU."""
    try:
        import onnxruntime
    except ImportError as err:
        raise TTSUnavailableError("onnxruntime is not installed.") from err

    model_dir = find_mms_dir(lang)
    if model_dir is None:
        raise TTSUnavailableError(
            f"No MMS voice for '{lang}'. Run ./run.py --download-models mayan."
        )
    vocabulary = json.loads((model_dir / _VOCABULARY_NAME).read_text("utf-8"))
    config_path = model_dir / _CONFIG_NAME
    config = json.loads(config_path.read_text("utf-8")) if config_path.is_file() else {}
    session = onnxruntime.InferenceSession(
        str(model_dir / MMS_ONNX_NAME), providers=["CPUExecutionProvider"]
    )
    return MmsVoice(
        session=session,
        vocabulary=vocabulary,
        sample_rate=int(config.get("sampling_rate", _DEFAULT_SAMPLE_RATE_HZ)),
    )
