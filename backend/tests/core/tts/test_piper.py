"""Unit tests for the neural Piper VITS voice backend (src/core/tts/piper.py).

Tests run hermetically in CI without downloading large ONNX weight checkpoints.
Assertions verify model discovery, JSON sanitization, multi-speaker routing,
in-memory streaming, and CLI fallback resilience.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.config import clear_settings_cache
from core.tts.espeak import TTSSynthesisError, TTSUnavailableError
from core.tts.piper import (
    PiperBackend,
    resolve_model_path,
    sanitize_model_config,
)

FAKE_PCM = b"\x00\x00" * 16000


@pytest.fixture(autouse=True)
def _clean_piper_settings(monkeypatch: pytest.MonkeyPatch):
    """Keeps Piper environment overrides hermetic between tests."""
    for name in (
        "TTS_ENABLED",
        "TTS_PIPER_BINARY",
        "TTS_PIPER_MODEL_DIR",
        "TTS_PIPER_MODEL_ES",
        "TTS_PIPER_MODEL_QUC",
        "TTS_PIPER_SPEAKER_ES",
        "TTS_PIPER_SPEAKER_QUC",
    ):
        monkeypatch.delenv(name, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_resolve_model_path_finds_file_in_custom_dir(tmp_path: Path):
    """Verifies custom directory takes highest priority in model search."""
    model_file = tmp_path / "custom-voice.onnx"
    model_file.write_bytes(b"dummy-weights")
    resolved = resolve_model_path("custom-voice.onnx", custom_dir=str(tmp_path))
    assert resolved == model_file.resolve()


def test_resolve_model_path_missing_raises_unavailable():
    """Verifies an absent model file raises TTSUnavailableError."""
    with pytest.raises(TTSUnavailableError, match="was not found"):
        resolve_model_path("non-existent-model-123.onnx")


def test_sanitize_model_config_normalizes_legacy_phoneme_type(tmp_path: Path):
    """Verifies PhonemeType.ESPEAK literal string is converted to 'espeak'."""
    cfg_file = tmp_path / "model.onnx.json"
    cfg_file.write_text(
        json.dumps({"phoneme_type": "PhonemeType.ESPEAK", "sample_rate": 22050}),
        encoding="utf-8",
    )
    sanitize_model_config(cfg_file)
    with open(cfg_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["phoneme_type"] == "espeak"


def test_sanitize_model_config_ignores_missing_or_corrupt_file(tmp_path: Path):
    """Verifies nonexistent or malformed JSON files do not raise exceptions."""
    sanitize_model_config(tmp_path / "missing.json")
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{corrupt-json", encoding="utf-8")
    sanitize_model_config(bad_file)


def test_piper_backend_is_available_and_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies is_available reflects TTS_ENABLED and model presence."""
    backend = PiperBackend()
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    assert backend.is_available() is False

    monkeypatch.setenv("TTS_ENABLED", "true")
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_PIPER_MODEL_ES", "nonexistent-model.onnx")
    clear_settings_cache()
    assert backend.is_available() is False

    (tmp_path / "custom-sharvard.onnx").write_bytes(b"weights")
    monkeypatch.setenv("TTS_PIPER_MODEL_ES", "custom-sharvard.onnx")
    clear_settings_cache()
    assert backend.is_available("es") is True
    assert backend.is_available("quc") is False

    (tmp_path / "quc_Latn-maya-medium.onnx").write_bytes(b"weights")
    assert backend.is_available("quc") is True


def test_synthesize_rejects_empty_or_disabled(monkeypatch: pytest.MonkeyPatch):
    """Verifies blank input or disabled state raises appropriate exceptions."""
    backend = PiperBackend()
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="disabled"):
        backend.synthesize("Hola clase")

    monkeypatch.setenv("TTS_ENABLED", "true")
    clear_settings_cache()
    with pytest.raises(TTSSynthesisError, match="no text to speak"):
        backend.synthesize("   ")


def test_synthesize_in_memory_generates_wav(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies in-memory synthesis calls PiperVoice and writes RIFF/WAV."""
    model_file = tmp_path / "es_ES-sharvard-medium.onnx"
    model_file.write_bytes(b"weights")
    (tmp_path / "es_ES-sharvard-medium.onnx.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()

    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = FAKE_PCM
    mock_voice = MagicMock()
    mock_voice.config.sample_rate = 22050
    mock_voice.synthesize.return_value = [mock_chunk]

    monkeypatch.setattr(
        "piper.voice.PiperVoice.load", MagicMock(return_value=mock_voice)
    )

    backend = PiperBackend()
    wav_bytes = backend.synthesize("Dividiste 6/8 mal.")

    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes[:16]
    assert len(wav_bytes) > len(FAKE_PCM)
    mock_voice.synthesize.assert_called_once()


def test_synthesize_falls_back_to_subprocess_on_in_memory_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies synthesis gracefully falls back to CLI subprocess."""
    model_file = tmp_path / "es_ES-sharvard-medium.onnx"
    model_file.write_bytes(b"weights")
    (tmp_path / "es_ES-sharvard-medium.onnx.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()

    backend = PiperBackend()
    monkeypatch.setattr(
        backend,
        "_synthesize_in_memory",
        MagicMock(side_effect=RuntimeError("in-memory error")),
    )

    fake_res = subprocess.CompletedProcess(
        args=["piper"], returncode=0, stdout=FAKE_PCM, stderr=b""
    )
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: fake_res)

    wav_bytes = backend.synthesize("Hola mundo.")
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes[:16]


def test_synthesize_subprocess_binary_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies subprocess raises TTSUnavailableError when binary is not found."""
    model_file = tmp_path / "es_ES-sharvard-medium.onnx"
    model_file.write_bytes(b"weights")
    (tmp_path / "es_ES-sharvard-medium.onnx.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()

    backend = PiperBackend()
    monkeypatch.setattr(
        backend,
        "_synthesize_in_memory",
        MagicMock(side_effect=RuntimeError("fail")),
    )
    monkeypatch.setattr("shutil.which", lambda name: None)

    with pytest.raises(TTSUnavailableError, match="not installed"):
        backend.synthesize("Hola mundo.")


def test_synthesize_subprocess_failure_raises_synthesis_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies subprocess non-zero exit code raises TTSSynthesisError."""
    model_file = tmp_path / "es_ES-sharvard-medium.onnx"
    model_file.write_bytes(b"weights")
    (tmp_path / "es_ES-sharvard-medium.onnx.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path))
    clear_settings_cache()

    backend = PiperBackend()
    monkeypatch.setattr(
        backend,
        "_synthesize_in_memory",
        MagicMock(side_effect=RuntimeError("fail")),
    )
    fake_res = subprocess.CompletedProcess(
        args=["piper"], returncode=1, stdout=b"", stderr=b"error"
    )
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/piper")
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: fake_res)

    with pytest.raises(TTSSynthesisError, match="code 1"):
        backend.synthesize("Hola mundo.")
