"""Unit tests for Qwen3-TTS neural speech synthesis backend."""

import platform
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


@pytest.fixture(autouse=True)
def _reset_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def _setup_mock_qwen_dir(base_dir: Path) -> tuple[Path, Path, Path]:
    models_dir = base_dir / "models" / "tts" / "qwen"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file = models_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model_file.write_bytes(b"dummy-model")
    mmproj_file = models_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    mmproj_file.write_bytes(b"dummy-mmproj")

    bin_name = "llama-tts.exe" if platform.system() == "Windows" else "llama-tts"
    bin_dir = base_dir / "bin" / "llama"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bin_file = bin_dir / bin_name
    bin_file.write_bytes(b"dummy-bin")

    return model_file, mmproj_file, bin_file


def test_qwen_properties():
    backend = QwenBackend()
    assert backend.engine_name == "qwen3-tts"
    assert not backend.is_loaded()


def test_qwen_is_available_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = QwenBackend()
    assert not backend.is_available()


def test_qwen_is_available_missing_files(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(tmp_path / "missing.gguf"))
    clear_settings_cache()
    backend = QwenBackend()
    assert not backend.is_available()


def test_qwen_is_available_success(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    backend = QwenBackend()
    assert backend.is_available()


def test_resolve_qwen_paths_success(monkeypatch, tmp_path):
    model, mmproj, bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    paths = resolve_qwen_paths()
    assert paths.model_path == model
    assert paths.mmproj_path == mmproj
    assert paths.bin_path == bin_file


def test_resolve_qwen_paths_relative_and_which(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    model, _mmproj, bin_file = _setup_mock_qwen_dir(tmp_path)
    bin_file.unlink()
    rel_model = Path("models/tts/qwen/Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf")

    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(rel_model))
    clear_settings_cache()

    with patch("shutil.which", return_value=str(tmp_path / "system-llama-tts")):
        paths = resolve_qwen_paths()
        assert paths.model_path.resolve() == model.resolve()
        assert paths.bin_path == tmp_path / "system-llama-tts"


def test_resolve_qwen_paths_failures(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(tmp_path / "ghost.gguf"))
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="model not found"):
        resolve_qwen_paths()

    model, mmproj, bin_file = _setup_mock_qwen_dir(tmp_path)
    mmproj.unlink()
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="mmproj not found"):
        resolve_qwen_paths()

    mmproj.write_bytes(b"dummy")
    bin_file.unlink()
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(TTSUnavailableError, match="not found on host"),
    ):
        resolve_qwen_paths()


def test_qwen_preload_and_unload(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    backend = QwenBackend()
    assert not backend.is_loaded()
    load_ms = backend.preload()
    assert load_ms >= 0.0
    assert backend.is_loaded()

    backend.unload()
    assert not backend.is_loaded()


def test_qwen_preload_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = QwenBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.preload()


def test_qwen_synthesize_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = QwenBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.synthesize("Hola")


def test_qwen_synthesize_empty_text():
    backend = QwenBackend()
    with pytest.raises(TTSSynthesisError, match="no text to speak"):
        backend.synthesize("   ")


def test_qwen_synthesize_success(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    backend = QwenBackend()

    def fake_subprocess_run(cmd, **kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_bytes(b"RIFF....WAVEfmt ....data....")
        res = MagicMock()
        res.returncode = 0
        res.stdout = "timings: prompt eval 0.04s + generation 0.3s"
        return res

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        audio = backend.synthesize("Hola mundo", voice="es")
        assert audio.startswith(b"RIFF")
        assert backend.is_loaded()


def test_qwen_synthesize_failure_returncode(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    backend = QwenBackend()
    bad_res = MagicMock(returncode=1, stdout="CUDA error: OOM")

    with (
        patch("subprocess.run", return_value=bad_res),
        pytest.raises(TTSSynthesisError, match="Qwen synthesis failed"),
    ):
        backend.synthesize("Hola")


def test_qwen_synthesize_zero_bytes(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    backend = QwenBackend()

    def fake_subprocess_run(cmd, **kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_bytes(b"")
        return MagicMock(returncode=0, stdout="ok")

    with (
        patch("subprocess.run", side_effect=fake_subprocess_run),
        pytest.raises(TTSSynthesisError, match="zero audio bytes"),
    ):
        backend.synthesize("Hola")


def test_qwen_synthesize_unexpected_error(monkeypatch, tmp_path):
    model, _mmproj, _bin_file = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path / "models" / "tts"))
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    backend = QwenBackend()
    with (
        patch("subprocess.run", side_effect=OSError("Exec failed")),
        pytest.raises(TTSSynthesisError, match="encountered error"),
    ):
        backend.synthesize("Hola")


def test_resolve_qwen_paths_ancestor_bin(monkeypatch, tmp_path):
    root = tmp_path / "deep" / "nested"
    model = root / "models" / "tts" / "qwen" / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"model")
    mmproj = model.parent / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    mmproj.write_bytes(b"mmproj")

    bin_name = "llama-tts.exe" if platform.system() == "Windows" else "llama-tts"
    bin_file = tmp_path / "bin" / "llama" / bin_name
    bin_file.parent.mkdir(parents=True, exist_ok=True)
    bin_file.write_bytes(b"bin")

    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    paths = resolve_qwen_paths()
    assert paths.bin_path == bin_file


@pytest.mark.parametrize(
    ("device_output", "expected_provider"),
    (("CUDA0: NVIDIA GeForce RTX", "cuda"), ("CPU0: host", "cpu")),
)
def test_detect_qwen_provider(device_output, expected_provider, tmp_path):
    """Reports the provider exposed by llama-tts rather than the requested ngl."""
    paths = QwenModelPaths(
        model_path=tmp_path / "model.gguf",
        mmproj_path=tmp_path / "mmproj.gguf",
        bin_path=tmp_path / "llama-tts.exe",
    )
    result = MagicMock(stdout=device_output, stderr="", returncode=0)

    with patch(
        "core.tts.engines.qwen.models.subprocess.run", return_value=result
    ) as run:
        assert detect_qwen_provider(paths) == expected_provider

    run.assert_called_once_with(
        [str(paths.bin_path), "--list-devices"],
        capture_output=True,
        text=True,
        timeout=5.0,
        check=False,
    )
