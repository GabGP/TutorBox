"""Unit tests for execution provider detection (CPU vs CUDA)."""

import ctypes
from unittest.mock import MagicMock, patch

import pytest

from core.tts.engines.provider import (
    configure_onnxruntime_dll_paths,
    is_cuda_available,
    resolve_execution_provider,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    is_cuda_available.cache_clear()
    yield
    is_cuda_available.cache_clear()


def test_resolve_provider_explicit_cuda():
    assert resolve_execution_provider("cuda") == "cuda"
    assert resolve_execution_provider(" CUDA ") == "cuda"


def test_resolve_provider_explicit_cpu():
    assert resolve_execution_provider("cpu") == "cpu"
    assert resolve_execution_provider(" CPU ") == "cpu"


def test_resolve_provider_auto_when_cuda_available():
    with patch("core.tts.engines.provider.is_cuda_available", return_value=True):
        assert resolve_execution_provider("auto") == "cuda"


def test_resolve_provider_auto_when_cuda_unavailable():
    with patch("core.tts.engines.provider.is_cuda_available", return_value=False):
        assert resolve_execution_provider("auto") == "cpu"


def test_is_cuda_available_no_hardware():
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.exists", return_value=False),
        patch.dict("os.environ", {}, clear=True),
    ):
        assert is_cuda_available() is False


def _mock_sherpa():
    return MagicMock(__file__="/fake/site-packages/sherpa_onnx/__init__.py")


def test_is_cuda_available_hardware_present_runtime_missing():
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.glob", return_value=[]),
    ):
        assert is_cuda_available() is False


def test_is_cuda_available_hardware_and_runtime_present():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll" if hasattr(ctypes, "WinDLL") else ".so"
    loader_target = "ctypes.WinDLL" if hasattr(ctypes, "WinDLL") else "ctypes.CDLL"
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch(loader_target, return_value=MagicMock()),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_loader_os_error():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll" if hasattr(ctypes, "WinDLL") else ".so"
    loader_target = "ctypes.WinDLL" if hasattr(ctypes, "WinDLL") else "ctypes.CDLL"
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch(loader_target, side_effect=OSError("missing dependency")),
    ):
        assert is_cuda_available() is False


def test_is_cuda_available_tegra_platform():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".so"

    def mock_exists(self):
        return self.as_posix() == "/dev/nvhost-ctrl"

    with (
        patch("shutil.which", return_value=None),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.exists", mock_exists),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("ctypes.CDLL", return_value=MagicMock()),
        patch("sys.platform", "linux"),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_cuda_visible_devices():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll" if hasattr(ctypes, "WinDLL") else ".so"
    loader_target = "ctypes.WinDLL" if hasattr(ctypes, "WinDLL") else "ctypes.CDLL"
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.exists", return_value=False),
        patch.dict("os.environ", {"CUDA_VISIBLE_DEVICES": "0"}),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch(loader_target, return_value=MagicMock()),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_runtime_import_failure():
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": None}),
    ):
        assert is_cuda_available() is False


def test_is_cuda_available_windows_platform():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll"
    loader_target = "ctypes.WinDLL" if hasattr(ctypes, "WinDLL") else "ctypes.CDLL"
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": _mock_sherpa()}),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("sys.platform", "win32"),
        patch(loader_target, return_value=MagicMock()),
    ):
        assert is_cuda_available() is True


def test_configure_onnxruntime_dll_paths_non_windows():
    with (
        patch("sys.platform", "linux"),
        patch("os.add_dll_directory") as mock_add_dll,
    ):
        configure_onnxruntime_dll_paths()
        mock_add_dll.assert_not_called()


def test_configure_onnxruntime_dll_paths_windows_success(tmp_path):
    mock_capi = tmp_path / "capi"
    mock_capi.mkdir(parents=True, exist_ok=True)
    fake_ort = MagicMock(__file__=str(tmp_path / "__init__.py"))

    with (
        patch("sys.platform", "win32"),
        patch.dict("sys.modules", {"onnxruntime": fake_ort}),
        patch("os.add_dll_directory") as mock_add_dll,
    ):
        configure_onnxruntime_dll_paths()
        mock_add_dll.assert_called_once_with(str(mock_capi))


def test_configure_onnxruntime_dll_paths_windows_missing_capi(tmp_path):
    fake_ort = MagicMock(__file__=str(tmp_path / "__init__.py"))

    with (
        patch("sys.platform", "win32"),
        patch.dict("sys.modules", {"onnxruntime": fake_ort}),
        patch("os.add_dll_directory") as mock_add_dll,
    ):
        configure_onnxruntime_dll_paths()
        mock_add_dll.assert_not_called()


def test_configure_onnxruntime_dll_paths_windows_error_handled():
    with (
        patch("sys.platform", "win32"),
        patch.dict("sys.modules", {"onnxruntime": None}),
    ):
        # Gracefully handles ImportError without crashing
        configure_onnxruntime_dll_paths()
