"""VITS metadata injection for Sherpa-ONNX model compatibility."""

import json
import logging
from pathlib import Path

import onnx

logger = logging.getLogger(__name__)


def ensure_sherpa_model(model_path: Path) -> Path:
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
