"""Model resolution and WAV encoding for Kokoro-82M neural TTS."""

import array
import io
import logging
import wave
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.exceptions import TTSUnavailableError

__all__ = [
    "KOKORO_SPANISH_SPEAKERS",
    "KokoroModelPaths",
    "resolve_kokoro_paths",
    "resolve_speaker_id",
    "samples_to_wav",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KokoroModelPaths:
    """Resolved file paths required by Kokoro-82M ONNX runtime."""

    model_path: Path
    voices_path: Path
    tokens_path: Path
    data_dir: Path
    dict_dir: Path | None
    lexicon_paths: tuple[Path, ...]


def _find_kokoro_dir(target_name: str) -> Path | None:
    """Searches standard paths for the Kokoro model directory."""
    tts = get_settings().tts
    candidate_dirs = [
        Path(target_name),
        PROJECT_ROOT / ".cache" / "models" / "tts" / target_name,
        Path(tts.piper_model_dir) / target_name,
        Path.cwd() / "models" / "tts" / target_name,
    ]
    for directory in candidate_dirs:
        if directory.is_dir():
            return directory.resolve()
    return None


def resolve_kokoro_paths(
    model_dir_name: str | None = None,
    model_file_name: str | None = None,
) -> KokoroModelPaths:
    """Resolves all file and directory paths for Kokoro-82M ONNX model."""
    tts_cfg = get_settings().tts
    target_name = model_dir_name or tts_cfg.kokoro_model_dir
    model_dir = _find_kokoro_dir(target_name)
    if not model_dir:
        raise TTSUnavailableError(
            f"Kokoro model directory '{target_name}' was not found in search paths."
        )

    pref = (model_file_name or tts_cfg.kokoro_model_file).strip()
    candidates = tuple(
        dict.fromkeys(filter(None, (pref, "model.onnx", "model.int8.onnx")))
    )
    model_file: Path | None = None
    for candidate in candidates:
        p = model_dir / candidate
        if p.is_file():
            model_file = p.resolve()
            break
    if not model_file:
        raise TTSUnavailableError(f"Kokoro ONNX model file not found in '{model_dir}'.")

    for required in ("voices.bin", "tokens.txt", "espeak-ng-data"):
        if not (model_dir / required).exists():
            raise TTSUnavailableError(
                f"Kokoro '{required}' not found in '{model_dir}'."
            )

    dict_candidate = model_dir / "dict"
    dict_dir = dict_candidate.resolve() if dict_candidate.is_dir() else None
    lexicons = tuple(
        (model_dir / name).resolve()
        for name in ("lexicon-us-en.txt", "lexicon-zh.txt")
        if (model_dir / name).is_file()
    )

    return KokoroModelPaths(
        model_path=model_file,
        voices_path=(model_dir / "voices.bin").resolve(),
        tokens_path=(model_dir / "tokens.txt").resolve(),
        data_dir=(model_dir / "espeak-ng-data").resolve(),
        dict_dir=dict_dir,
        lexicon_paths=lexicons,
    )


def samples_to_wav(
    samples: Sequence[float],
    sample_rate: int,
    target_peak: float = 0.78,
) -> bytes:
    """Converts float audio samples into RIFF/WAV bytes with calibrated peak amplitude."""
    max_amp = max((abs(s) for s in samples), default=0.0)
    scale = (target_peak / max_amp) if (max_amp > 0.0 and target_peak > 0.0) else 1.0

    int16_samples = array.array(
        "h", (int(max(-1.0, min(1.0, s * scale)) * 32767) for s in samples)
    )
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int16_samples.tobytes())
    return buf.getvalue()


KOKORO_SPANISH_SPEAKERS: dict[str, int] = {
    "ef_dora": 28,
    "dora": 28,
    "em_alex": 29,
    "alex": 29,
    "em_santa": 53,
    "santa": 53,
}


def resolve_speaker_id(voice: str | None, default_id: int = 53) -> int:
    """Maps voice names or digit strings to Kokoro speaker IDs."""
    if voice:
        cleaned = voice.strip().lower()
        if cleaned in KOKORO_SPANISH_SPEAKERS:
            return KOKORO_SPANISH_SPEAKERS[cleaned]
        try:
            return int(cleaned)
        except ValueError:
            pass
    return default_id
