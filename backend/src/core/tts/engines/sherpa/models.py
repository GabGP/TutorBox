"""Model resolution, tokens generation, and WAV encoding for Sherpa-ONNX."""

import json
import logging
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.audio import samples_to_wav
from core.tts.exceptions import TTSUnavailableError

try:
    import onnx
except ImportError:
    onnx = None  # type: ignore[assignment]

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


def _ensure_sherpa_model(model_path: Path) -> Path:
    """Ensures ONNX model has required VITS metadata (sample_rate, voice, etc.) for Sherpa."""
    if onnx is None:
        return model_path

    clean_name = model_path.name.replace(".sherpa.onnx", ".onnx")
    sherpa_name = clean_name.replace(".onnx", ".sherpa.onnx")
    sherpa_target = model_path.parent / sherpa_name

    target_check = sherpa_target if sherpa_target.is_file() else model_path
    try:
        mdl = onnx.load(str(target_check), load_external_data=False)
        metadata_keys = {prop.key for prop in mdl.metadata_props}
        if "sample_rate" in metadata_keys:
            return target_check
    except Exception as err:  # noqa: BLE001
        logger.debug("Failed to inspect ONNX metadata for %s: %s", target_check, err)
        return model_path

    clean_stem = clean_name.replace(".onnx", "")
    json_path = model_path.parent / f"{clean_stem}.onnx.json"
    if not json_path.is_file():
        return model_path

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        sample_rate = str(cfg.get("audio", {}).get("sample_rate", 22050))
        voice = str(cfg.get("espeak", {}).get("voice", "es"))
        num_speakers = str(cfg.get("num_speakers", 1))

        base_onnx = model_path.parent / clean_name
        src_path = base_onnx if base_onnx.is_file() else model_path
        model_obj = onnx.load(str(src_path))
        existing_keys = {prop.key for prop in model_obj.metadata_props}

        meta_entries = {
            "sample_rate": sample_rate,
            "n_speakers": num_speakers,
            "model_type": "vits",
            "comment": "piper",
            "language": voice,
            "voice": voice,
            "has_espeak": "1",
        }
        for k, v in meta_entries.items():
            if k not in existing_keys:
                prop = model_obj.metadata_props.add()
                prop.key = k
                prop.value = v

        onnx.save(model_obj, str(sherpa_target))
        logger.info(
            "Generated Sherpa-compatible ONNX model with metadata: %s",
            sherpa_target.name,
        )
        return sherpa_target
    except Exception as err:  # noqa: BLE001
        logger.warning("Failed to inject Sherpa metadata into %s: %s", model_path, err)
        return model_path


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
