"""Model resolution and WAV encoding for Kokoro-82M neural TTS."""

import logging
from dataclasses import dataclass
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.audio import samples_to_wav
from core.tts.exceptions import TTSUnavailableError

__all__ = [
    "DEFAULT_KOKORO_SPEAKER_ID",
    "KOKORO_SPANISH_SPEAKERS",
    "KOKORO_SPEAKER_ALEX",
    "KOKORO_SPEAKER_DORA",
    "KOKORO_SPEAKER_SANTA",
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
    candidate_dirs = (
        Path(target_name),
        PROJECT_ROOT / ".cache" / "models" / "tts" / target_name,
        Path(tts.piper_model_dir) / target_name,
        Path.cwd() / "models" / "tts" / target_name,
    )
    return next((d.resolve() for d in candidate_dirs if d.is_dir()), None)


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


KOKORO_SPEAKER_DORA: int = 28
KOKORO_SPEAKER_ALEX: int = 29
KOKORO_SPEAKER_SANTA: int = 53
DEFAULT_KOKORO_SPEAKER_ID: int = KOKORO_SPEAKER_SANTA

KOKORO_SPANISH_SPEAKERS: dict[str, int] = {
    "ef_dora": KOKORO_SPEAKER_DORA,
    "dora": KOKORO_SPEAKER_DORA,
    "em_alex": KOKORO_SPEAKER_ALEX,
    "alex": KOKORO_SPEAKER_ALEX,
    "em_santa": KOKORO_SPEAKER_SANTA,
    "santa": KOKORO_SPEAKER_SANTA,
}


def resolve_speaker_id(
    voice: str | None, default_id: int = DEFAULT_KOKORO_SPEAKER_ID
) -> int:
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
