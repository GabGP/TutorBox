"""Model resolution, tokens generation, and WAV encoding for Sherpa-ONNX."""

import json
import logging
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.audio import samples_to_wav
from core.tts.engines.sherpa.metadata import ensure_sherpa_model as _ensure_sherpa_model
from core.tts.exceptions import TTSUnavailableError

__all__ = ["resolve_sherpa_paths", "samples_to_wav"]

logger = logging.getLogger(__name__)


def _find_espeak_data(base_dir: Path) -> Path | None:
    """Finds espeak-ng-data directory from local models, piper package, or system."""
    candidates = [
        base_dir / "espeak-ng-data",
        PROJECT_ROOT / ".cache" / "models" / "tts" / "espeak-ng-data",
    ]
    try:
        import importlib.util

        spec = importlib.util.find_spec("piper")
        if spec and spec.origin:
            candidates.append(Path(spec.origin).parent / "espeak-ng-data")
    except (ImportError, AttributeError):
        pass

    candidates.extend(
        [Path("/usr/share/espeak-ng-data"), Path("/usr/lib/espeak-ng-data")]
    )

    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def _ensure_tokens_file(model_path: Path) -> Path:
    """Finds tokens.txt or generates it from piper .onnx.json phoneme_id_map."""
    tokens_candidates = [
        model_path.parent / f"tokens_{model_path.stem}.txt",
        model_path.parent / "tokens.txt",
        model_path.parent / f"tokens_{model_path.name.replace('.sherpa', '')}.txt",
    ]
    for cand in tokens_candidates:
        if cand.is_file():
            return cand.resolve()

    clean_stem = model_path.name.replace(".sherpa", "").replace(".onnx", "")
    json_path = model_path.parent / f"{clean_stem}.onnx.json"
    if json_path.is_file():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            phoneme_map = data.get("phoneme_id_map", {})
            if phoneme_map:
                out_tokens = model_path.parent / f"tokens_{clean_stem}.txt"
                with open(out_tokens, "w", encoding="utf-8") as f:
                    f.writelines(
                        f"{token} {ids[0]}\n" for token, ids in phoneme_map.items()
                    )
                return out_tokens.resolve()
        except (OSError, json.JSONDecodeError) as err:
            logger.warning("Failed to generate tokens from %s: %s", json_path, err)

    raise TTSUnavailableError(
        f"Sherpa tokens file not found for model '{model_path.name}'."
    )


def resolve_sherpa_paths(model_name: str) -> tuple[Path, Path, Path]:
    """Resolves (model_path, tokens_path, espeak_data_dir) for Sherpa-ONNX."""
    tts = get_settings().tts
    search_dirs = [
        Path(tts.piper_model_dir),
        PROJECT_ROOT / ".cache" / "models" / "tts",
        Path.cwd() / "models" / "tts",
    ]

    sherpa_stem = model_name.replace(".onnx", ".sherpa.onnx")
    candidates = [sherpa_stem, model_name]

    resolved_model: Path | None = None
    for directory in search_dirs:
        for name in candidates:
            cand = directory / name
            if cand.is_file():
                resolved_model = cand.resolve()
                break
        if resolved_model:
            break

    if not resolved_model:
        raise TTSUnavailableError(
            f"Sherpa model '{model_name}' was not found in search paths."
        )

    resolved_model = _ensure_sherpa_model(resolved_model)
    tokens_path = _ensure_tokens_file(resolved_model)
    data_dir = _find_espeak_data(resolved_model.parent)
    if not data_dir:
        raise TTSUnavailableError("espeak-ng-data directory was not found for Sherpa.")

    return resolved_model, tokens_path, data_dir
