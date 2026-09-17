"""Edge-case coverage for Qwen3-TTS options and host discovery."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import clear_settings_cache
from core.tts.engines.qwen import QwenBackend
from core.tts.engines.qwen.models import (
    QwenModelPaths,
    detect_qwen_provider,
    resolve_qwen_paths,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from tests.core.tts.test_qwen import _setup_mock_qwen_dir


@pytest.fixture(autouse=True)
def _reset_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def _configure_model(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path]:
    model, mmproj, binary = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    return model, mmproj, binary


def test_qwen_passes_context_seed_and_reference_voice(monkeypatch, tmp_path):
    model, _mmproj, _binary = _configure_model(monkeypatch, tmp_path)
    speaker = tmp_path / "teacher.wav"
    speaker.write_bytes(b"speaker")
    monkeypatch.setenv("TTS_QWEN_CONTEXT", "2048")
    monkeypatch.setenv("TTS_QWEN_SEED", "7")
    monkeypatch.setenv("TTS_QWEN_SPEAKER_FILE", str(speaker))
    clear_settings_cache()

    def fake_run(cmd, **_kwargs):
        output = Path(cmd[cmd.index("-o") + 1])
        output.write_bytes(b"RIFF-WAVE")
        return MagicMock(returncode=0, stdout="ok")

    with patch(
        "core.tts.engines.qwen.engine.subprocess.run", side_effect=fake_run
    ) as run:
        QwenBackend().synthesize("Hola", voice="es")

    command = run.call_args.args[0]
    assert command[command.index("-c") + 1] == "2048"
    assert command[command.index("-s") + 1] == "7"
    assert command[-2:] == ["--tts-speaker-file", str(speaker)]
    assert model.exists()


def test_qwen_rejects_missing_reference_voice(monkeypatch, tmp_path):
    _configure_model(monkeypatch, tmp_path)
    monkeypatch.setenv("TTS_QWEN_SPEAKER_FILE", str(tmp_path / "missing.wav"))
    clear_settings_cache()

    with pytest.raises(TTSUnavailableError, match="speaker file not found"):
        QwenBackend().synthesize("Hola")


def test_qwen_converts_timeout_to_domain_error(monkeypatch, tmp_path):
    _configure_model(monkeypatch, tmp_path)
    with (
        patch(
            "core.tts.engines.qwen.engine.subprocess.run",
            side_effect=subprocess.TimeoutExpired("llama-tts", 10),
        ),
        pytest.raises(TTSSynthesisError, match="timed out"),
    ):
        QwenBackend().synthesize("Hola")


def test_qwen_finds_model_in_default_project_cache(monkeypatch, tmp_path):
    model_dir = tmp_path / ".cache" / "models" / "tts" / "qwen"
    model_dir.mkdir(parents=True)
    model = model_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model.write_bytes(b"model")
    (model_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf").write_bytes(b"mmproj")
    binary = tmp_path / "bin" / "llama" / "llama-tts.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"binary")
    monkeypatch.setattr("core.tts.engines.qwen.models.PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", "")
    clear_settings_cache()

    paths = resolve_qwen_paths()
    assert paths.model_path == model
    assert paths.bin_path == binary


def test_qwen_returns_none_when_default_model_candidates_are_missing(
    monkeypatch, tmp_path
):
    monkeypatch.setattr("core.tts.engines.qwen.models.PROJECT_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TTS_PIPER_MODEL_DIR", str(tmp_path / "empty-model-dir"))
    clear_settings_cache()

    with pytest.raises(TTSUnavailableError, match="model not found"):
        resolve_qwen_paths()


def test_qwen_uses_configured_binary_path(monkeypatch, tmp_path):
    model, _mmproj, _binary = _configure_model(monkeypatch, tmp_path)
    configured = tmp_path / "custom" / "llama-tts.exe"
    configured.parent.mkdir()
    configured.write_bytes(b"binary")
    monkeypatch.setenv("TTS_QWEN_BINARY", str(configured))
    clear_settings_cache()

    assert resolve_qwen_paths().bin_path == configured
    assert model.exists()


def test_qwen_searches_linux_install_locations(monkeypatch, tmp_path):
    model, _mmproj, _binary = _configure_model(monkeypatch, tmp_path)
    fake_binary = tmp_path / "llama-tts"
    fake_binary.write_bytes(b"binary")
    monkeypatch.setenv("TTS_QWEN_BINARY", "")
    monkeypatch.setattr("core.tts.engines.qwen.models.platform.system", lambda: "Linux")
    clear_settings_cache()

    with patch(
        "core.tts.engines.qwen.models.shutil.which", return_value=str(fake_binary)
    ):
        assert resolve_qwen_paths().bin_path == fake_binary
    assert model.exists()


def test_qwen_provider_defaults_to_cpu_on_probe_error(tmp_path):
    paths = QwenModelPaths(
        tmp_path / "model", tmp_path / "mmproj", tmp_path / "llama-tts"
    )
    with patch(
        "core.tts.engines.qwen.models.subprocess.run",
        side_effect=OSError("probe failed"),
    ):
        assert detect_qwen_provider(paths) == "cpu"
