"""NVIDIA GPU memory via NVML loaded with ctypes, falling back to PyTorch CUDA."""

from __future__ import annotations

import ctypes

from tools.benchmark.tts.shared.units import BYTES_PER_MB

NVML_LIBRARY_NAMES = ("nvml.dll", "libnvidia-ml.so", "libnvidia-ml.so.1")


class NVMLMemory(ctypes.Structure):
    """Mirrors the nvmlMemory_t struct filled by nvmlDeviceGetMemoryInfo."""

    _fields_ = [
        ("total", ctypes.c_ulonglong),
        ("free", ctypes.c_ulonglong),
        ("used", ctypes.c_ulonglong),
    ]


class NVMLTracker:
    """Lightweight ctypes wrapper for querying NVIDIA GPU memory via NVML."""

    def __init__(self) -> None:
        self._handle: ctypes.c_void_p | None = None
        self._nvml: ctypes.CDLL | None = None
        for library_name in NVML_LIBRARY_NAMES:
            try:
                nvml_library = ctypes.CDLL(library_name)
                nvml_library.nvmlInit_v2()
                handle = ctypes.c_void_p()
                nvml_library.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(handle))
                self._nvml = nvml_library
                self._handle = handle
                break
            except Exception:  # noqa: BLE001, S112
                # The NVML library is optional: any failure means "try the next name".
                continue

    def get_vram_mb(self) -> float:
        """Returns GPU VRAM allocated in MB, or 0.0 if CUDA is unavailable."""
        if self._nvml and self._handle:
            try:
                memory_info = NVMLMemory()
                self._nvml.nvmlDeviceGetMemoryInfo(
                    self._handle, ctypes.byref(memory_info)
                )
                return float(memory_info.used) / BYTES_PER_MB
            except Exception:  # noqa: BLE001, S110
                # The NVML query is optional: any failure falls through to PyTorch.
                pass

        try:
            import torch

            if torch.cuda.is_available():
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return float(total_bytes - free_bytes) / BYTES_PER_MB
        except Exception:  # noqa: BLE001, S110
            # PyTorch is optional: a missing or CUDA-less install means "0.0 MB".
            pass
        return 0.0

    def close(self) -> None:
        """Shuts down NVML library context."""
        if self._nvml:
            try:
                self._nvml.nvmlShutdown()
            except Exception:  # noqa: BLE001, S110
                # A failing shutdown must not stop the tracker from forgetting the library.
                pass
            self._nvml = None
            self._handle = None
