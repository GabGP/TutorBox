"""Unit tests for execution provider detection (CPU vs CUDA)."""

from unittest.mock import MagicMock, patch

import pytest

from core.tts.engines.provider import is_cuda_available, resolve_execution_provider


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


def test_is_cuda_available_hardware_present_runtime_missing():
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("pathlib.Path.glob", return_value=[]),
    ):
        assert is_cuda_available() is False


def test_is_cuda_available_hardware_and_runtime_present():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll"
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("ctypes.WinDLL", return_value=MagicMock()),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_loader_os_error():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll"
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("ctypes.WinDLL", side_effect=OSError("missing dependency")),
    ):
        assert is_cuda_available() is False


def test_is_cuda_available_tegra_platform():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".so"

    def mock_exists(self):
        return self.as_posix() == "/dev/nvhost-ctrl"

    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.exists", mock_exists),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("ctypes.CDLL", return_value=MagicMock()),
        patch("sys.platform", "linux"),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_cuda_visible_devices():
    mock_cuda_lib = MagicMock()
    mock_cuda_lib.suffix = ".dll"
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.exists", return_value=False),
        patch.dict("os.environ", {"CUDA_VISIBLE_DEVICES": "0"}),
        patch("pathlib.Path.glob", return_value=[mock_cuda_lib]),
        patch("ctypes.WinDLL", return_value=MagicMock()),
    ):
        assert is_cuda_available() is True


def test_is_cuda_available_runtime_import_failure():
    with (
        patch("shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch.dict("sys.modules", {"sherpa_onnx": None}),
    ):
        assert is_cuda_available() is False
