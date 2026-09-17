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


def _setup_mock_qwen_dir(
    base_dir: Path, with_daemon: bool = False
) -> tuple[Path, Path, Path, Path | None]:
    models_dir = base_dir / "models" / "tts" / "qwen"
    models_dir.mkdir(parents=True, exist_ok=True)
    model = models_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model.write_bytes(b"dummy-model")
    mmproj = models_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    mmproj.write_bytes(b"dummy-mmproj")

    ext = ".exe" if platform.system() == "Windows" else ""
    bin_dir = base_dir / "bin" / "llama.cpp"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bin_file = bin_dir / f"llama-tts{ext}"
    bin_file.write_bytes(b"dummy-bin")

    daemon_bin = None
    if with_daemon:
        daemon_bin = bin_dir / f"llama-tts-daemon{ext}"
        daemon_bin.write_bytes(b"dummy-daemon")

    return model, mmproj, bin_file, daemon_bin


def test_qwen_properties():
    backend = QwenBackend()
    assert backend.engine_name == "qwen3-tts"
    assert not backend.is_loaded()


def test_qwen_is_available_states(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    assert not QwenBackend().is_available()

    monkeypatch.setenv("TTS_ENABLED", "true")
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(tmp_path / "missing.gguf"))
    clear_settings_cache()
    assert not QwenBackend().is_available()

    model, _, _, _ = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    assert QwenBackend().is_available()


def test_resolve_qwen_paths_success(monkeypatch, tmp_path):
    model, mmproj, bin_file, _ = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    paths = resolve_qwen_paths()
    assert paths.model_path == model and paths.mmproj_path == mmproj
    assert paths.bin_path == bin_file


def test_resolve_qwen_paths_failures(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(tmp_path / "ghost.gguf"))
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="model not found"):
        resolve_qwen_paths()

    model, mmproj, bin_file, _ = _setup_mock_qwen_dir(tmp_path)
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
    model, _, _, _ = _setup_mock_qwen_dir(tmp_path, with_daemon=False)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    backend = QwenBackend()
    assert backend.preload() >= 0.0 and backend.is_loaded()
    backend.unload()
    assert not backend.is_loaded()

    mock_client = MagicMock()
    mock_client.is_alive.return_value = True
    model, _, _, _ = _setup_mock_qwen_dir(tmp_path, with_daemon=True)
    with patch(
        "core.tts.engines.qwen.engine.QwenDaemonClient", return_value=mock_client
    ):
        backend = QwenBackend()
        assert backend.preload() >= 0.0 and backend.is_loaded()
        backend.unload()
        mock_client.close.assert_called_once()

    with patch(
        "core.tts.engines.qwen.engine.QwenDaemonClient",
        side_effect=TTSUnavailableError("daemon fail"),
    ):
        backend = QwenBackend()
        assert backend.preload() >= 0.0 and backend.is_loaded()
        assert backend._daemon_client is None


def test_qwen_disabled_and_empty(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = QwenBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.preload()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.synthesize("Hola")
    monkeypatch.setenv("TTS_ENABLED", "true")
    clear_settings_cache()
    with pytest.raises(TTSSynthesisError, match="no text to speak"):
        QwenBackend().synthesize("   ")


def test_qwen_synthesize_cli_and_daemon(monkeypatch, tmp_path):
    model, _, _, _ = _setup_mock_qwen_dir(tmp_path, with_daemon=False)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()

    def fake_run(cmd, **kwargs):
        Path(cmd[cmd.index("-o") + 1]).write_bytes(b"RIFF....WAVEfmt ....data....")
        return MagicMock(returncode=0, stdout="prompt eval 0.04s + generation 0.3s")

    with patch("subprocess.run", side_effect=fake_run):
        audio = QwenBackend().synthesize("Hola mundo", voice="es")
        assert audio.startswith(b"RIFF")

    backend = QwenBackend()
    mock_client = MagicMock()
    mock_client.is_alive.return_value = True

    def fake_synth(lang, out_wav, text, timeout_seconds=10.0):
        out_wav.write_bytes(b"RIFF....WAVEfmt ....data....")
        return "DONE\ttotal=0.812\tprompt_eval=0.081\tgeneration=0.589\tvocoder=0.142"

    mock_client.synthesize.side_effect = fake_synth
    backend._daemon_client = mock_client
    audio = backend.synthesize("Hola mundo", voice="es")
    assert audio.startswith(b"RIFF") and backend.last_synthesis_seconds == 0.812

    # Test auto-preload on synthesis when daemon binary is present
    model, _, _, _ = _setup_mock_qwen_dir(tmp_path, with_daemon=True)
    auto_backend = QwenBackend()
    with patch(
        "core.tts.engines.qwen.engine.QwenDaemonClient", return_value=mock_client
    ):
        auto_audio = auto_backend.synthesize("Hola auto", voice="es")
        assert auto_audio.startswith(b"RIFF")


def test_qwen_synthesize_errors(monkeypatch, tmp_path):
    model, _, _, _ = _setup_mock_qwen_dir(tmp_path)
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    bad_res = MagicMock(returncode=1, stdout="CUDA error: OOM")
    with (
        patch("subprocess.run", return_value=bad_res),
        pytest.raises(TTSSynthesisError, match="Qwen synthesis failed"),
    ):
        QwenBackend().synthesize("Hola")

    def fake_empty(cmd, **kwargs):
        Path(cmd[cmd.index("-o") + 1]).write_bytes(b"")
        return MagicMock(returncode=0, stdout="ok")

    with (
        patch("subprocess.run", side_effect=fake_empty),
        pytest.raises(TTSSynthesisError, match="zero audio bytes"),
    ):
        QwenBackend().synthesize("Hola")

    with (
        patch("subprocess.run", side_effect=OSError("fail")),
        pytest.raises(TTSSynthesisError, match="Qwen synthesis error"),
    ):
        QwenBackend().synthesize("Hola")


def test_resolve_qwen_paths_ancestor_bin(monkeypatch, tmp_path):
    root = tmp_path / "deep" / "nested"
    model = root / "models" / "tts" / "qwen" / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"model")
    mmproj = model.parent / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    mmproj.write_bytes(b"mmproj")
    ext = ".exe" if platform.system() == "Windows" else ""
    bin_file = tmp_path / "bin" / "llama.cpp" / f"llama-tts{ext}"
    bin_file.parent.mkdir(parents=True, exist_ok=True)
    bin_file.write_bytes(b"bin")
    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))
    clear_settings_cache()
    assert resolve_qwen_paths().bin_path == bin_file


@pytest.mark.parametrize(
    ("device_output", "expected_provider"),
    (("CUDA0: NVIDIA GeForce RTX", "cuda"), ("CPU0: host", "cpu")),
)
def test_detect_qwen_provider(device_output, expected_provider, tmp_path):
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
        encoding="utf-8",
        errors="replace",
        timeout=5.0,
        check=False,
    )
