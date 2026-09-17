"""Unit tests for Kokoro-82M offline speech synthesis backend."""

from unittest.mock import MagicMock, patch

import pytest

from core.config import clear_settings_cache
from core.tts.engines.kokoro import KokoroBackend
from core.tts.engines.kokoro.models import (
    resolve_kokoro_paths,
    samples_to_wav,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError


@pytest.fixture(autouse=True)
def _reset_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def _setup_mock_kokoro_dir(base_dir, has_dict=True, has_lexicon=True):
    k_dir = base_dir / "kokoro-test"
    k_dir.mkdir(parents=True, exist_ok=True)
    (k_dir / "model.int8.onnx").write_text("dummy model")
    (k_dir / "voices.bin").write_text("dummy voices")
    (k_dir / "tokens.txt").write_text("dummy tokens")
    (k_dir / "espeak-ng-data").mkdir(parents=True, exist_ok=True)
    if has_dict:
        (k_dir / "dict").mkdir(parents=True, exist_ok=True)
    if has_lexicon:
        (k_dir / "lexicon-us-en.txt").write_text("dummy lexicon")
    return k_dir


def test_kokoro_properties():
    backend = KokoroBackend()
    assert backend.engine_name == "kokoro"
    assert not backend.is_loaded()


def test_kokoro_is_available_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = KokoroBackend()
    assert not backend.is_available()


def test_kokoro_is_available_import_error():
    backend = KokoroBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": None}):
        assert not backend.is_available()


def test_kokoro_is_available_model_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(tmp_path / "missing"))
    clear_settings_cache()
    backend = KokoroBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": MagicMock()}):
        assert not backend.is_available()


def test_samples_to_wav():
    samples = [-1.5, -0.5, 0.0, 0.5, 1.5]
    wav_bytes = samples_to_wav(samples, 24000, target_peak=0.78)
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes[:16]

    empty_wav = samples_to_wav([], 24000)
    assert empty_wav.startswith(b"RIFF")


def test_resolve_kokoro_paths_success(tmp_path):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    paths = resolve_kokoro_paths(str(k_dir))
    assert paths.model_path.is_file()
    assert paths.voices_path.is_file()
    assert paths.tokens_path.is_file()
    assert paths.data_dir.is_dir()
    assert paths.dict_dir is not None
    assert len(paths.lexicon_paths) >= 1


def test_resolve_kokoro_paths_fallback_onnx(tmp_path):
    k_dir = _setup_mock_kokoro_dir(tmp_path, has_dict=False, has_lexicon=False)
    (k_dir / "model.int8.onnx").unlink()
    (k_dir / "model.onnx").write_text("model onnx")
    paths = resolve_kokoro_paths(str(k_dir))
    assert paths.model_path.name == "model.onnx"
    assert paths.dict_dir is None
    assert len(paths.lexicon_paths) == 0


def test_resolve_kokoro_paths_failures(tmp_path):
    with pytest.raises(TTSUnavailableError, match="was not found in search paths"):
        resolve_kokoro_paths(str(tmp_path / "ghost"))

    k_dir = _setup_mock_kokoro_dir(tmp_path)
    (k_dir / "model.int8.onnx").unlink()
    with pytest.raises(TTSUnavailableError, match="model file not found"):
        resolve_kokoro_paths(str(k_dir))

    k_dir = _setup_mock_kokoro_dir(tmp_path)
    (k_dir / "voices.bin").unlink()
    with pytest.raises(TTSUnavailableError, match="voices.bin"):
        resolve_kokoro_paths(str(k_dir))

    k_dir = _setup_mock_kokoro_dir(tmp_path)
    (k_dir / "tokens.txt").unlink()
    with pytest.raises(TTSUnavailableError, match="tokens.txt"):
        resolve_kokoro_paths(str(k_dir))

    k_dir = _setup_mock_kokoro_dir(tmp_path)
    (k_dir / "espeak-ng-data").rmdir()
    with pytest.raises(TTSUnavailableError, match="espeak-ng-data"):
        resolve_kokoro_paths(str(k_dir))


def test_kokoro_preload_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = KokoroBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.preload()


def test_kokoro_preload_import_error():
    backend = KokoroBackend()
    with (
        patch.dict("sys.modules", {"sherpa_onnx": None}),
        pytest.raises(TTSUnavailableError, match="not installed"),
    ):
        backend.preload()


def test_kokoro_preload_init_failure_cpu(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    monkeypatch.setenv("TTS_KOKORO_PROVIDER", "cpu")
    clear_settings_cache()

    backend = KokoroBackend()
    mock_sherpa = MagicMock()
    mock_sherpa.OfflineTts.side_effect = RuntimeError("Broken CPU model")
    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSUnavailableError, match="Failed to initialize"),
    ):
        backend.preload()


def test_kokoro_preload_cuda_fallback_to_cpu(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    monkeypatch.setenv("TTS_KOKORO_PROVIDER", "cuda")
    clear_settings_cache()

    backend = KokoroBackend()
    mock_sherpa = MagicMock()
    mock_sherpa.OfflineTts.side_effect = [RuntimeError("No CUDA"), MagicMock()]
    with patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}):
        assert backend.preload() >= 0
        assert backend.is_loaded()


def test_kokoro_lifecycle_and_synthesize(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    clear_settings_cache()

    backend = KokoroBackend()
    mock_sherpa = MagicMock()
    mock_engine = MagicMock()
    mock_audio = MagicMock()
    mock_audio.samples = [0.1, 0.2, -0.1]
    mock_audio.sample_rate = 24000
    mock_engine.generate.return_value = mock_audio
    mock_sherpa.OfflineTts.return_value = mock_engine

    with patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}):
        assert not backend.is_loaded()
        load_ms = backend.preload()
        assert load_ms >= 0
        assert backend.is_loaded()

        wav = backend.synthesize("Hola prueba", voice="53")
        assert wav.startswith(b"RIFF")
        assert mock_engine.generate.called
        assert mock_engine.generate.call_args[1]["sid"] == 53

        wav_dora = backend.synthesize("Hola Dora", voice="ef_dora")
        assert wav_dora.startswith(b"RIFF")
        assert mock_engine.generate.call_args[1]["sid"] == 28

        wav_fallback = backend.synthesize("Hola de nuevo", voice="invalid")
        assert wav_fallback.startswith(b"RIFF")

        backend.unload()
        assert not backend.is_loaded()


def test_kokoro_synthesize_empty_text():
    backend = KokoroBackend()
    with pytest.raises(TTSSynthesisError, match="no text to speak"):
        backend.synthesize("    ")


def test_kokoro_synthesize_zero_samples(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    clear_settings_cache()

    backend = KokoroBackend()
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


def test_kokoro_synthesize_engine_error(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    clear_settings_cache()

    backend = KokoroBackend()
    mock_sherpa = MagicMock()
    mock_engine = MagicMock()
    mock_engine.generate.side_effect = RuntimeError("Crash")
    mock_sherpa.OfflineTts.return_value = mock_engine

    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSSynthesisError, match="Kokoro synthesis failed"),
    ):
        backend.synthesize("Hola")


def test_kokoro_is_available_success(tmp_path, monkeypatch):
    k_dir = _setup_mock_kokoro_dir(tmp_path)
    monkeypatch.setenv("TTS_KOKORO_MODEL_DIR", str(k_dir))
    clear_settings_cache()
    backend = KokoroBackend()
    with patch.dict("sys.modules", {"sherpa_onnx": MagicMock()}):
        assert backend.is_available()


def test_kokoro_synthesize_disabled(monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    backend = KokoroBackend()
    with pytest.raises(TTSUnavailableError, match="Speech synthesis is disabled"):
        backend.synthesize("Hola")


def test_kokoro_synthesize_uninitialized():
    backend = KokoroBackend()
    backend.preload = MagicMock(return_value=0.0)  # type: ignore[method-assign]
    with pytest.raises(TTSUnavailableError, match="Kokoro engine is not initialized"):
        backend.synthesize("Hola")
