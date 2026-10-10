"""Verifies NVML library loading, VRAM readings, the PyTorch fallback and shutdown."""

import ctypes
import sys
from types import SimpleNamespace

from tools.benchmark.tts.memory.nvml import NVML_LIBRARY_NAMES, NVMLTracker
from tools.benchmark.tts.shared.units import BYTES_PER_MB


def megabytes_as_bytes(megabytes: float) -> int:
    """Converts megabytes to a whole byte count, as NVML and PyTorch report it."""
    return int(megabytes * BYTES_PER_MB)


class FakeNVMLLibrary:
    """Stands in for a loaded NVML shared library and records the calls it receives."""

    def __init__(
        self,
        used_bytes: int = 0,
        handle_value: int | None = 1,
        init_error: Exception | None = None,
        query_error: Exception | None = None,
        shutdown_error: Exception | None = None,
    ) -> None:
        self.calls: list[str] = []
        self._used_bytes = used_bytes
        self._handle_value = handle_value
        self._init_error = init_error
        self._query_error = query_error
        self._shutdown_error = shutdown_error

    def nvmlInit_v2(self) -> None:
        self.calls.append("nvmlInit_v2")
        if self._init_error is not None:
            raise self._init_error

    def nvmlDeviceGetHandleByIndex_v2(
        self, device_index: int, handle_reference
    ) -> None:
        self.calls.append("nvmlDeviceGetHandleByIndex_v2")
        if self._handle_value is not None:
            handle_reference._obj.value = self._handle_value

    def nvmlDeviceGetMemoryInfo(self, handle, memory_reference) -> None:
        self.calls.append("nvmlDeviceGetMemoryInfo")
        if self._query_error is not None:
            raise self._query_error
        memory_reference._obj.used = self._used_bytes

    def nvmlShutdown(self) -> None:
        self.calls.append("nvmlShutdown")
        if self._shutdown_error is not None:
            raise self._shutdown_error


def install_fake_cdll(
    monkeypatch, libraries_by_name: dict[str, FakeNVMLLibrary]
) -> list[str]:
    """Makes ctypes.CDLL return the fake libraries by name and fail for every other name."""
    attempted_names: list[str] = []

    def load_library(library_name: str) -> FakeNVMLLibrary:
        attempted_names.append(library_name)
        if library_name not in libraries_by_name:
            raise OSError
        return libraries_by_name[library_name]

    monkeypatch.setattr(ctypes, "CDLL", load_library)
    return attempted_names


def install_fake_torch(
    monkeypatch,
    cuda_available: bool = True,
    free_bytes: int = 0,
    total_bytes: int = 0,
) -> list[str]:
    """Installs a fake torch module and returns the list recording its CUDA queries."""
    torch_calls: list[str] = []

    def is_available() -> bool:
        torch_calls.append("is_available")
        return cuda_available

    def mem_get_info() -> tuple[int, int]:
        torch_calls.append("mem_get_info")
        return free_bytes, total_bytes

    fake_cuda = SimpleNamespace(is_available=is_available, mem_get_info=mem_get_info)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=fake_cuda))
    return torch_calls


def test_first_library_that_fails_is_skipped_for_the_next_name(monkeypatch):
    """Verifies a library that fails to load is skipped and the next name is used."""
    second_library = FakeNVMLLibrary()
    attempted = install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[1]: second_library})
    tracker = NVMLTracker()
    assert attempted == list(NVML_LIBRARY_NAMES[:2])
    assert tracker._nvml is second_library


def test_first_library_that_loads_wins(monkeypatch):
    """Verifies no later library name is tried once one has loaded."""
    first_library = FakeNVMLLibrary()
    attempted = install_fake_cdll(
        monkeypatch,
        {
            NVML_LIBRARY_NAMES[0]: first_library,
            NVML_LIBRARY_NAMES[1]: FakeNVMLLibrary(),
        },
    )
    tracker = NVMLTracker()
    assert attempted == [NVML_LIBRARY_NAMES[0]]
    assert tracker._nvml is first_library


def test_library_failing_at_init_is_skipped(monkeypatch):
    """Verifies a library whose nvmlInit_v2 raises is skipped for the next name."""
    failing_library = FakeNVMLLibrary(init_error=OSError())
    working_library = FakeNVMLLibrary()
    install_fake_cdll(
        monkeypatch,
        {
            NVML_LIBRARY_NAMES[0]: failing_library,
            NVML_LIBRARY_NAMES[1]: working_library,
        },
    )
    tracker = NVMLTracker()
    assert tracker._nvml is working_library


def test_no_library_loads_leaves_the_tracker_without_nvml(monkeypatch):
    """Verifies that when no NVML library loads, the tracker holds no library or handle."""
    attempted = install_fake_cdll(monkeypatch, {})
    tracker = NVMLTracker()
    assert attempted == list(NVML_LIBRARY_NAMES)
    assert tracker._nvml is None
    assert tracker._handle is None


def test_unfilled_handle_skips_nvml_queries(monkeypatch):
    """Verifies an NVML handle that stays empty is never queried for memory."""
    library = FakeNVMLLibrary(handle_value=None)
    install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[0]: library})
    install_fake_torch(
        monkeypatch,
        free_bytes=megabytes_as_bytes(4),
        total_bytes=megabytes_as_bytes(10),
    )
    assert NVMLTracker().get_vram_mb() == 6.0
    assert "nvmlDeviceGetMemoryInfo" not in library.calls


def test_nvml_used_memory_is_reported_in_megabytes(monkeypatch):
    """Verifies the NVML used-memory figure is converted to MB and PyTorch is not used."""
    library = FakeNVMLLibrary(used_bytes=megabytes_as_bytes(2))
    install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[0]: library})
    torch_calls = install_fake_torch(monkeypatch, total_bytes=megabytes_as_bytes(100))
    assert NVMLTracker().get_vram_mb() == 2.0
    assert torch_calls == []


def test_nvml_query_error_falls_back_to_torch(monkeypatch):
    """Verifies an NVML memory query that raises falls back to PyTorch CUDA numbers."""
    library = FakeNVMLLibrary(query_error=OSError())
    install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[0]: library})
    install_fake_torch(
        monkeypatch,
        free_bytes=megabytes_as_bytes(4),
        total_bytes=megabytes_as_bytes(10),
    )
    assert NVMLTracker().get_vram_mb() == 6.0


def test_torch_cuda_reports_total_minus_free_in_megabytes(monkeypatch):
    """Verifies the PyTorch fallback reports total minus free memory in MB."""
    install_fake_cdll(monkeypatch, {})
    install_fake_torch(
        monkeypatch,
        free_bytes=megabytes_as_bytes(4),
        total_bytes=megabytes_as_bytes(10),
    )
    assert NVMLTracker().get_vram_mb() == 6.0


def test_torch_without_cuda_reports_zero(monkeypatch):
    """Verifies a PyTorch install without CUDA reports 0.0 without querying memory."""
    install_fake_cdll(monkeypatch, {})
    torch_calls = install_fake_torch(monkeypatch, cuda_available=False)
    assert NVMLTracker().get_vram_mb() == 0.0
    assert torch_calls == ["is_available"]


def test_missing_torch_reports_zero(monkeypatch):
    """Verifies a machine without PyTorch installed reports 0.0."""
    install_fake_cdll(monkeypatch, {})
    monkeypatch.setitem(sys.modules, "torch", None)
    assert NVMLTracker().get_vram_mb() == 0.0


def test_close_shuts_nvml_down_and_forgets_the_library(monkeypatch):
    """Verifies close() calls nvmlShutdown and clears the library and handle."""
    library = FakeNVMLLibrary()
    install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[0]: library})
    tracker = NVMLTracker()
    tracker.close()
    assert library.calls[-1] == "nvmlShutdown"
    assert tracker._nvml is None
    assert tracker._handle is None


def test_close_survives_a_failing_shutdown(monkeypatch):
    """Verifies a shutdown that raises still clears the library and handle."""
    library = FakeNVMLLibrary(shutdown_error=OSError())
    install_fake_cdll(monkeypatch, {NVML_LIBRARY_NAMES[0]: library})
    tracker = NVMLTracker()
    tracker.close()
    assert tracker._nvml is None
    assert tracker._handle is None


def test_close_without_a_library_does_nothing(monkeypatch):
    """Verifies close() on a tracker with no NVML library neither fails nor shuts down."""
    install_fake_cdll(monkeypatch, {})
    tracker = NVMLTracker()
    tracker.close()
    assert tracker._nvml is None
