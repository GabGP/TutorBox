"""Converts a downloaded Piper voice into the files Sherpa-ONNX expects."""

import json
from pathlib import Path

from tools.voice_models.console import TAG_OK, TAG_WARN


def generate_sherpa_tokens(onnx_json_path: Path, output_tokens_path: Path) -> bool:
    """Generates tokens text file from Piper phoneme mapping for Sherpa compatibility."""
    if output_tokens_path.is_file() and output_tokens_path.stat().st_size > 0:
        return True
    if not onnx_json_path.is_file():
        return False
    try:
        with open(onnx_json_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        phoneme_map = data.get("phoneme_id_map", {})
        if not phoneme_map:
            return False
        with open(output_tokens_path, "w", encoding="utf-8") as file_handle:
            file_handle.writelines(
                f"{token} {ids[0]}\n" for token, ids in phoneme_map.items()
            )
        print(f"{TAG_OK} Generated Sherpa tokens: {output_tokens_path.name}")
        return True
    except (OSError, json.JSONDecodeError) as err:
        print(f"{TAG_WARN} Could not generate tokens: {err}")
        return False


def _build_vits_metadata(piper_config: dict) -> dict[str, str]:
    """Maps the Piper voice config onto the metadata keys Sherpa-ONNX reads."""
    sample_rate = str(piper_config.get("audio", {}).get("sample_rate", 22050))
    voice = str(piper_config.get("espeak", {}).get("voice", "es"))
    num_speakers = str(piper_config.get("num_speakers", 1))
    return {
        "sample_rate": sample_rate,
        "n_speakers": num_speakers,
        "model_type": "vits",
        "comment": "piper",
        "language": voice,
        "voice": voice,
        "has_espeak": "1",
    }


def generate_sherpa_model(
    onnx_path: Path, onnx_json_path: Path, output_sherpa_path: Path, force: bool = False
) -> bool:
    """Injects VITS metadata into Piper ONNX model for Sherpa-ONNX compatibility."""
    if (
        output_sherpa_path.is_file()
        and output_sherpa_path.stat().st_size > 0
        and not force
    ):
        return True
    if not onnx_path.is_file() or not onnx_json_path.is_file():
        return False
    try:
        import onnx

        with open(onnx_json_path, "r", encoding="utf-8") as file_handle:
            piper_config = json.load(file_handle)

        model = onnx.load(str(onnx_path))
        existing_keys = {entry.key for entry in model.metadata_props}
        for metadata_key, metadata_value in _build_vits_metadata(piper_config).items():
            if metadata_key not in existing_keys:
                new_entry = model.metadata_props.add()
                new_entry.key = metadata_key
                new_entry.value = metadata_value

        onnx.save(model, str(output_sherpa_path))
        print(f"{TAG_OK} Generated Sherpa model: {output_sherpa_path.name}")
        return True
    except Exception as err:  # noqa: BLE001
        print(f"{TAG_WARN} Could not generate Sherpa model metadata: {err}")
        return False
