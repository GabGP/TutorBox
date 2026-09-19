"""Unit tests for Sherpa-ONNX metadata injection."""

import json
from unittest.mock import MagicMock, patch

from core.tts.engines.sherpa import metadata


def test_ensure_sherpa_model_onnx_none(tmp_path):
    fake_model = tmp_path / "model.onnx"
    fake_model.write_text("dummy")
    with patch.object(metadata, "onnx", None):
        assert metadata.ensure_sherpa_model(fake_model) == fake_model


def test_ensure_sherpa_model_already_has_sample_rate(tmp_path):
    mock_model = tmp_path / "model.onnx"
    mock_model.write_text("dummy")
    mock_prop = MagicMock()
    mock_prop.key = "sample_rate"
    mock_onnx_model = MagicMock()
    mock_onnx_model.metadata_props = [mock_prop]

    with patch.object(metadata.onnx, "load", return_value=mock_onnx_model):
        res = metadata.ensure_sherpa_model(mock_model)
        assert res == mock_model


def test_ensure_sherpa_model_load_exception(tmp_path):
    mock_model = tmp_path / "corrupt.onnx"
    mock_model.write_text("dummy")
    with patch.object(metadata.onnx, "load", side_effect=RuntimeError("Corrupt ONNX")):
        assert metadata.ensure_sherpa_model(mock_model) == mock_model


def test_ensure_sherpa_model_missing_json(tmp_path):
    mock_model = tmp_path / "model_no_json.onnx"
    mock_model.write_text("dummy")
    mock_onnx_model = MagicMock()
    mock_onnx_model.metadata_props = []

    with patch.object(metadata.onnx, "load", return_value=mock_onnx_model):
        assert metadata.ensure_sherpa_model(mock_model) == mock_model


def test_ensure_sherpa_model_successful_injection(tmp_path):
    model_file = tmp_path / "test.onnx"
    model_file.write_text("dummy")
    json_file = tmp_path / "test.onnx.json"
    json_file.write_text(
        json.dumps(
            {
                "audio": {"sample_rate": 22050},
                "espeak": {"voice": "es"},
                "num_speakers": 1,
            }
        )
    )

    mock_onnx_model = MagicMock()
    mock_props = MagicMock()
    mock_props.__iter__.return_value = []
    mock_props.add.return_value = MagicMock()
    mock_onnx_model.metadata_props = mock_props

    with (
        patch.object(metadata.onnx, "load", return_value=mock_onnx_model),
        patch.object(metadata.onnx, "save") as mock_save,
    ):
        res = metadata.ensure_sherpa_model(model_file)
        assert res.name == "test.sherpa.onnx"
        mock_save.assert_called_once()


def test_ensure_sherpa_model_injection_save_error(tmp_path):
    model_file = tmp_path / "test_err.onnx"
    model_file.write_text("dummy")
    json_file = tmp_path / "test_err.onnx.json"
    json_file.write_text(json.dumps({"audio": {"sample_rate": 22050}}))

    mock_onnx_model = MagicMock()
    mock_onnx_model.metadata_props = []

    with (
        patch.object(metadata.onnx, "load", return_value=mock_onnx_model),
        patch.object(metadata.onnx, "save", side_effect=OSError("Disk write error")),
    ):
        assert metadata.ensure_sherpa_model(model_file) == model_file
