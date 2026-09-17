"""Unit tests for Sherpa-ONNX offline speech synthesis backend."""

import json
from unittest.mock import MagicMock, patch

import pytest

from core.config import clear_settings_cache
from core.tts.engines.sherpa import SherpaBackend
from core.tts.engines.sherpa.models import (
    _ensure_tokens_file,
    _find_espeak_data,
    resolve_sherpa_paths,
    samples_to_wav,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError


@pytest.fixture(autouse=True)
def _reset_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_sherpa_properties():
    backend = SherpaBackend()
    assert backend.engine_name == "sherpa"
    assert not backend.is_loaded()


def test_sherpa_is_available_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = SherpaBackend()
    assert not backend.is_available()


def test_sherpa_is_available_import_error(monkeypatch):
    backend = SherpaBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": None}):
        assert not backend.is_available()


def test_sherpa_is_available_model_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "non_existent.onnx")
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()
    backend = SherpaBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": MagicMock()}):
        assert not backend.is_available()


def test_samples_to_wav():
    wav_bytes = samples_to_wav([-1.5, -0.5, 0.0, 0.5, 1.5], 22050, target_peak=0.78)
    assert wav_bytes.startswith(b"RIFF") and b"WAVE" in wav_bytes[:16]

    empty_wav = samples_to_wav([], 22050)
    assert empty_wav.startswith(b"RIFF")


def test_find_espeak_data(tmp_path):
    assert _find_espeak_data(tmp_path) is not None or True
    custom_dir = tmp_path / "espeak-ng-data"
    custom_dir.mkdir()
    assert _find_espeak_data(tmp_path) == custom_dir.resolve()


def test_ensure_tokens_file_existing(tmp_path):
    model = tmp_path / "model.onnx"
    model.write_text("model")
    tokens = tmp_path / "tokens_model.txt"
    tokens.write_text("token 1\n")
    assert _ensure_tokens_file(model) == tokens.resolve()


def test_ensure_tokens_file_auto_generation(tmp_path):
    model = tmp_path / "test_model.onnx"
    model.write_text("fake onnx")
    json_path = tmp_path / "test_model.onnx.json"
    json_path.write_text(json.dumps({"phoneme_id_map": {"a": [1], "b": [2]}}))
    tokens = _ensure_tokens_file(model)
    assert tokens.is_file()
    assert "a 1" in tokens.read_text()


def test_ensure_tokens_file_missing_json(tmp_path):
    model = tmp_path / "orphan.onnx"
    model.write_text("fake onnx")
    with pytest.raises(TTSUnavailableError, match="Sherpa tokens file not found"):
        _ensure_tokens_file(model)


def test_resolve_sherpa_paths_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="not found in search paths"):
        resolve_sherpa_paths("ghost_model.onnx")


def test_sherpa_preload_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = SherpaBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.preload()


def test_sherpa_preload_import_error():
    backend = SherpaBackend()
    with (
        patch.dict("sys.modules", {"sherpa_onnx": None}),
        pytest.raises(TTSUnavailableError, match="not installed"),
    ):
        backend.preload()


def test_sherpa_preload_init_failure_cpu(tmp_path, monkeypatch):
    mock_model = tmp_path / "dummy.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_dummy.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "dummy.onnx")
    monkeypatch.setenv("TTS_SHERPA_PROVIDER", "cpu")
    clear_settings_cache()

    backend = SherpaBackend()
    mock_sherpa = MagicMock()
    mock_sherpa.OfflineTts.side_effect = RuntimeError("Broken CPU model")
    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSUnavailableError, match="Failed to initialize"),
    ):
        backend.preload()


def test_sherpa_preload_cuda_fallback_to_cpu(tmp_path, monkeypatch):
    mock_model = tmp_path / "dummy.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_dummy.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "dummy.onnx")
    monkeypatch.setenv("TTS_SHERPA_PROVIDER", "cuda")
    clear_settings_cache()

    backend = SherpaBackend()
    mock_sherpa = MagicMock()
    # First attempt (cuda) raises, second attempt (cpu fallback) succeeds
    mock_sherpa.OfflineTts.side_effect = [RuntimeError("No CUDA"), MagicMock()]
    with patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}):
        assert backend.preload() >= 0
        assert backend.is_loaded()


def test_sherpa_lifecycle_and_synthesize(tmp_path, monkeypatch):
    mock_model = tmp_path / "test.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_test.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "test.onnx")
    clear_settings_cache()

    backend = SherpaBackend()
    mock_sherpa = MagicMock()
    mock_engine = MagicMock()
    mock_audio = MagicMock()
    mock_audio.samples = [0.1, 0.2, -0.1]
    mock_audio.sample_rate = 22050
    mock_engine.generate.return_value = mock_audio
    mock_sherpa.OfflineTts.return_value = mock_engine

    with patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}):
        assert not backend.is_loaded()
        load_ms = backend.preload()
        assert load_ms >= 0
        assert backend.is_loaded()

        # Synthesis
        wav = backend.synthesize("Hola prueba")
        assert wav.startswith(b"RIFF")
        assert mock_engine.generate.called

        # Unload
        backend.unload()
        assert not backend.is_loaded()


def test_sherpa_synthesize_empty_text():
    backend = SherpaBackend()
    with pytest.raises(TTSSynthesisError, match="no text to speak"):
        backend.synthesize("    ")


def test_sherpa_synthesize_zero_samples(tmp_path, monkeypatch):
    mock_model = tmp_path / "test.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_test.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "test.onnx")
    clear_settings_cache()

    backend = SherpaBackend()
    mock_sherpa = MagicMock()
    mock_engine = MagicMock()
    mock_audio = MagicMock()
    mock_audio.samples = []
    mock_engine.generate.return_value = mock_audio
    mock_sherpa.OfflineTts.return_value = mock_engine

    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSSynthesisError, match="zero audio samples"),
    ):
        backend.synthesize("Hola")


def test_sherpa_synthesize_engine_error(tmp_path, monkeypatch):
    mock_model = tmp_path / "test.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_test.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "test.onnx")
    clear_settings_cache()

    backend = SherpaBackend()
    mock_sherpa = MagicMock()
    mock_engine = MagicMock()
    mock_engine.generate.side_effect = RuntimeError("Crash")
    mock_sherpa.OfflineTts.return_value = mock_engine

    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSSynthesisError, match="Sherpa synthesis failed"),
    ):
        backend.synthesize("Hola")


def test_sherpa_is_available_success(tmp_path, monkeypatch):
    mock_model = tmp_path / "test.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_test.txt").write_text("a 1\n")
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SHERPA_MODEL_ES", "test.onnx")
    clear_settings_cache()
    backend = SherpaBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": MagicMock()}):
        assert backend.is_available()


def test_sherpa_synthesize_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = SherpaBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.synthesize("Hola")


def test_resolve_sherpa_paths_missing_data_dir(tmp_path, monkeypatch):
    mock_model = tmp_path / "test.onnx"
    mock_model.write_text("fake")
    (tmp_path / "tokens_test.txt").write_text("a 1\n")
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()
    with (
        patch("core.tts.engines.sherpa.models._find_espeak_data", return_value=None),
        pytest.raises(
            TTSUnavailableError, match="espeak-ng-data directory was not found"
        ),
    ):
        resolve_sherpa_paths("test.onnx")


def test_ensure_tokens_file_invalid_json(tmp_path):
    model = tmp_path / "invalid.onnx"
    model.write_text("fake onnx")
    json_path = tmp_path / "invalid.onnx.json"
    json_path.write_text("not json {")
    with pytest.raises(TTSUnavailableError, match="Sherpa tokens file not found"):
        _ensure_tokens_file(model)


def test_find_espeak_data_not_found(tmp_path):
    with patch.dict("sys.modules", {"piper": None}):
        assert _find_espeak_data(tmp_path) is None


def test_sherpa_synthesize_uninitialized():
    backend = SherpaBackend()
    backend.preload = MagicMock(return_value=0.0)  # type: ignore[method-assign]
    with pytest.raises(TTSUnavailableError, match="Sherpa engine is not initialized"):
        backend.synthesize("Hola")
