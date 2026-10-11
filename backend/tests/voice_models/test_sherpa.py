"""Unit tests for the Piper to Sherpa-ONNX conversion (tools/voice_models/sherpa.py)."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tools.voice_models import sherpa


class _FakeMetadataProps(list):
    """Stands in for the protobuf repeated field that holds ONNX metadata."""

    def add(self) -> SimpleNamespace:
        new_entry = SimpleNamespace(key="", value="")
        self.append(new_entry)
        return new_entry


def _fake_onnx_module(existing_metadata: dict[str, str]) -> MagicMock:
    """Builds a fake onnx module whose loaded model carries the given metadata."""
    metadata_props = _FakeMetadataProps(
        SimpleNamespace(key=key, value=value)
        for key, value in existing_metadata.items()
    )
    fake_onnx = MagicMock()
    fake_onnx.load.return_value = SimpleNamespace(metadata_props=metadata_props)
    return fake_onnx


def _write_piper_voice(tmp_path, piper_config: dict):
    """Writes a stand-in Piper model and its JSON config, returning both paths."""
    onnx_path = tmp_path / "voice.onnx"
    onnx_path.write_bytes(b"onnx-weights")
    json_path = tmp_path / "voice.onnx.json"
    json_path.write_text(json.dumps(piper_config), encoding="utf-8")
    return onnx_path, json_path


def test_generate_sherpa_tokens_creates_tokens(tmp_path):
    """Verifies generate_sherpa_tokens extracts phoneme_id_map to formatted lines."""
    json_path = tmp_path / "model.onnx.json"
    tokens_path = tmp_path / "tokens.txt"
    json_path.write_text(
        json.dumps({"phoneme_id_map": {"a": [1], "b": [2], "_": [0]}}),
        encoding="utf-8",
    )

    success = sherpa.generate_sherpa_tokens(json_path, tokens_path)
    assert success is True
    assert tokens_path.is_file()
    lines = tokens_path.read_text(encoding="utf-8").splitlines()
    assert "a 1" in lines
    assert "b 2" in lines


def test_generate_sherpa_tokens_missing_json(tmp_path):
    """Verifies generate_sherpa_tokens returns False when json config does not exist."""
    json_path = tmp_path / "nonexistent.json"
    tokens_path = tmp_path / "tokens.txt"
    assert sherpa.generate_sherpa_tokens(json_path, tokens_path) is False


def test_generate_sherpa_tokens_keeps_existing_tokens_file(tmp_path):
    """Verifies an existing tokens file is left untouched and reported as success."""
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("a 1\n", encoding="utf-8")

    assert sherpa.generate_sherpa_tokens(tmp_path / "absent.json", tokens_path) is True
    assert tokens_path.read_text(encoding="utf-8") == "a 1\n"


def test_generate_sherpa_tokens_rejects_config_without_phoneme_map(tmp_path):
    """Verifies a config with no phoneme_id_map writes nothing and returns False."""
    json_path = tmp_path / "model.onnx.json"
    json_path.write_text(json.dumps({"audio": {}}), encoding="utf-8")
    tokens_path = tmp_path / "tokens.txt"

    assert sherpa.generate_sherpa_tokens(json_path, tokens_path) is False
    assert not tokens_path.exists()


def test_generate_sherpa_tokens_reports_malformed_json(tmp_path, capsys):
    """Verifies a config that is not valid JSON is reported instead of raising."""
    json_path = tmp_path / "model.onnx.json"
    json_path.write_text("{not json", encoding="utf-8")

    assert sherpa.generate_sherpa_tokens(json_path, tmp_path / "tokens.txt") is False
    assert "Could not generate tokens" in capsys.readouterr().out


def test_generate_sherpa_model_keeps_existing_output(tmp_path):
    """Verifies an existing Sherpa model is kept when force is off."""
    sherpa_path = tmp_path / "voice.sherpa.onnx"
    sherpa_path.write_bytes(b"already-converted")

    result = sherpa.generate_sherpa_model(
        tmp_path / "absent.onnx", tmp_path / "absent.json", sherpa_path
    )
    assert result is True
    assert sherpa_path.read_bytes() == b"already-converted"


def test_generate_sherpa_model_requires_model_and_config(tmp_path):
    """Verifies conversion is refused when the Piper model or config is missing."""
    result = sherpa.generate_sherpa_model(
        tmp_path / "absent.onnx", tmp_path / "absent.json", tmp_path / "out.onnx"
    )
    assert result is False


def test_generate_sherpa_model_adds_only_missing_metadata(tmp_path):
    """Verifies VITS metadata is filled from the config without overwriting existing keys."""
    onnx_path, json_path = _write_piper_voice(
        tmp_path,
        {"audio": {"sample_rate": 16000}, "espeak": {"voice": "es-419"}},
    )
    sherpa_path = tmp_path / "voice.sherpa.onnx"
    fake_onnx = _fake_onnx_module({"comment": "kept-as-is"})

    with patch.dict(sys.modules, {"onnx": fake_onnx}):
        result = sherpa.generate_sherpa_model(onnx_path, json_path, sherpa_path)

    assert result is True
    saved_model, saved_path = fake_onnx.save.call_args[0]
    assert saved_path == str(sherpa_path)
    assert {entry.key: entry.value for entry in saved_model.metadata_props} == {
        "comment": "kept-as-is",
        "sample_rate": "16000",
        "n_speakers": "1",
        "model_type": "vits",
        "language": "es-419",
        "voice": "es-419",
        "has_espeak": "1",
    }


def test_generate_sherpa_model_force_regenerates_existing_output(tmp_path):
    """Verifies force=True converts again even when the Sherpa model already exists."""
    onnx_path, json_path = _write_piper_voice(tmp_path, {})
    sherpa_path = tmp_path / "voice.sherpa.onnx"
    sherpa_path.write_bytes(b"stale")
    fake_onnx = _fake_onnx_module({})

    with patch.dict(sys.modules, {"onnx": fake_onnx}):
        result = sherpa.generate_sherpa_model(
            onnx_path, json_path, sherpa_path, force=True
        )

    assert result is True
    saved_model = fake_onnx.save.call_args[0][0]
    metadata = {entry.key: entry.value for entry in saved_model.metadata_props}
    assert metadata["sample_rate"] == "22050"
    assert metadata["voice"] == "es"


def test_generate_sherpa_model_reports_conversion_failure(tmp_path, capsys):
    """Verifies a failing ONNX load is reported as a warning instead of raising."""
    onnx_path, json_path = _write_piper_voice(tmp_path, {})
    fake_onnx = MagicMock()
    fake_onnx.load.side_effect = ValueError("corrupt graph")

    with patch.dict(sys.modules, {"onnx": fake_onnx}):
        result = sherpa.generate_sherpa_model(
            onnx_path, json_path, tmp_path / "voice.sherpa.onnx"
        )

    assert result is False
    assert "Could not generate Sherpa model metadata" in capsys.readouterr().out
