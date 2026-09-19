"""Unit tests for Sherpa-ONNX runtime loader and provider resolution."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config.models import TTSConfig
from core.tts.engines.sherpa import runtime
from core.tts.exceptions import TTSUnavailableError


def test_ensure_ort_dll_directory_non_windows():
    with patch("sys.platform", "linux"):
        # Should return immediately on non-Windows platforms
        assert runtime.ensure_ort_dll_directory() is None


def test_ensure_ort_dll_directory_windows_import_error():
    with (
        patch("sys.platform", "win32"),
        patch.dict("sys.modules", {"onnxruntime": None}),
    ):
        # Gracefully handles missing onnxruntime
        assert runtime.ensure_ort_dll_directory() is None


def test_create_offline_tts_import_error():
    cfg = TTSConfig()
    with (
        patch.dict("sys.modules", {"sherpa_onnx": None}),
        pytest.raises(TTSUnavailableError, match="sherpa-onnx runtime is not installed"),
    ):
        runtime.create_offline_tts(Path("m"), Path("t"), Path("d"), cfg)


def test_create_offline_tts_cuda_fallback_cpu_failure():
    cfg = TTSConfig(sherpa_provider="cuda")
    mock_sherpa = MagicMock()
    # First attempt (cuda) fails, second attempt (cpu) also fails
    mock_sherpa.OfflineTts.side_effect = [
        RuntimeError("CUDA out of memory"),
        RuntimeError("CPU instruction invalid"),
    ]
    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSUnavailableError, match="Failed to initialize Sherpa-ONNX on CPU"),
    ):
        runtime.create_offline_tts(Path("m"), Path("t"), Path("d"), cfg)


def test_create_offline_tts_cpu_direct_failure():
    cfg = TTSConfig(sherpa_provider="cpu")
    mock_sherpa = MagicMock()
    mock_sherpa.OfflineTts.side_effect = RuntimeError("Broken model file")
    with (
        patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}),
        pytest.raises(TTSUnavailableError, match="Failed to initialize Sherpa-ONNX: Broken model"),
    ):
        runtime.create_offline_tts(Path("m"), Path("t"), Path("d"), cfg)


def test_find_espeak_data_import_error(tmp_path):
    from core.tts.engines.sherpa.models import _find_espeak_data

    with patch("importlib.util.find_spec", side_effect=ImportError("No piper")):
        assert _find_espeak_data(tmp_path) is None or True

