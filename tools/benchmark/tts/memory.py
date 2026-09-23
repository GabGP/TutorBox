"""Cross-platform memory monitor for TTS speech synthesis benchmarking.

Tracks both Host CPU RAM (Resident Set Size including child process tree)
and GPU Device VRAM (via NVML or PyTorch fallback). Identifies NVIDIA
Jetson Unified Memory Architecture (UMA) versus discrete GPU PC configurations.
"""

from __future__ import annotations

import ctypes
import os
import platform
import sys
import threading
import time
from pathlib import Path
from typing import Any

__all__ = [
    "BYTES_PER_MB",
    "MemoryMonitor",
    "NVMLTracker",
    "get_host_rss_mb",
    "is_jetson_uma",
]

BYTES_PER_MB: float = 1024.0 * 1024.0
KILOBYTES_PER_MB: float = 1024.0
DEFAULT_SAMPLE_INTERVAL_SECONDS: float = 0.01


def is_jetson_uma() -> bool:
    """Returns True if the runtime platform is an NVIDIA Jetson (Tegra UMA)."""
    if Path("/etc/nv_tegra_release").exists():
        return True
    if sys.platform.startswith("linux") and platform.machine() == "aarch64":
        soc = Path("/sys/devices/soc0/family")
        if soc.exists() and "tegra" in soc.read_text(encoding="utf-8").lower():
            return True
    return False


def get_host_rss_mb(include_children: bool = True) -> float:
    """Returns host RAM resident set size in MB for process and its children."""
    try:
        import psutil  # pyright: ignore[reportMissingImports]

        proc = psutil.Process()
        total_rss = proc.memory_info().rss
        if include_children:
            try:
                for child in proc.children(recursive=True):
                    total_rss += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return float(total_rss) / BYTES_PER_MB
    except (ImportError, AttributeError):
        pass

    if sys.platform == "win32":
        try:
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t),
                ]

            get_mem_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_mem_info.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
                wintypes.DWORD,
            ]
            get_mem_info.restype = wintypes.BOOL
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            if get_mem_info(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(counters),
                counters.cb,
            ):
                return float(counters.WorkingSetSize) / BYTES_PER_MB
        except Exception:
            pass

    return 0.0


class NVMLTracker:
    """Lightweight ctypes wrapper for querying NVIDIA GPU memory via NVML."""

    def __init__(self) -> None:
        self._handle: ctypes.c_void_p | None = None
        self._nvml: ctypes.CDLL | None = None
        for lib in ("nvml.dll", "libnvidia-ml.so", "libnvidia-ml.so.1"):
            try:
                nvml = ctypes.CDLL(lib)
                nvml.nvmlInit_v2()
                handle = ctypes.c_void_p()
                nvml.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(handle))
                self._nvml = nvml
                self._handle = handle
                break
            except Exception:
                continue

    def get_vram_mb(self) -> float:
        """Returns GPU VRAM allocated in MB, or 0.0 if CUDA is unavailable."""
        if self._nvml and self._handle:
            try:
                class NVMLMemory(ctypes.Structure):
                    _fields_ = [
                        ("total", ctypes.c_ulonglong),
                        ("free", ctypes.c_ulonglong),
                        ("used", ctypes.c_ulonglong),
                    ]

                mem = NVMLMemory()
                self._nvml.nvmlDeviceGetMemoryInfo(self._handle, ctypes.byref(mem))
                return float(mem.used) / BYTES_PER_MB
            except Exception:
                pass

        try:
            import torch

            if torch.cuda.is_available():
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return float(total_bytes - free_bytes) / BYTES_PER_MB
        except Exception:
            pass
        return 0.0

    def close(self) -> None:
        """Shuts down NVML library context."""
        if self._nvml:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass
            self._nvml = None
            self._handle = None


class MemoryMonitor:
    """Context manager for tracking peak Host RAM and GPU VRAM during synthesis."""

    def __init__(
        self, sample_interval_s: float = DEFAULT_SAMPLE_INTERVAL_SECONDS
    ) -> None:
        self.sample_interval_s = sample_interval_s
        self.nvml = NVMLTracker()
        self.is_uma = is_jetson_uma()

        self.baseline_rss_mb: float = get_host_rss_mb()
        self.baseline_vram_mb: float = self.nvml.get_vram_mb()

        self.peak_rss_mb: float = self.baseline_rss_mb
        self.peak_vram_mb: float = self.baseline_vram_mb

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)

    def _sample_loop(self) -> None:
        while not self._stop.is_set():
            rss = get_host_rss_mb()
            vram = self.nvml.get_vram_mb()
            if rss > self.peak_rss_mb:
                self.peak_rss_mb = rss
            if vram > self.peak_vram_mb:
                self.peak_vram_mb = vram
            time.sleep(self.sample_interval_s)

    def __enter__(self) -> MemoryMonitor:
        self._thread.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        final_rss = get_host_rss_mb()
        final_vram = self.nvml.get_vram_mb()
        if final_rss > self.peak_rss_mb:
            self.peak_rss_mb = final_rss
        if final_vram > self.peak_vram_mb:
            self.peak_vram_mb = final_vram
        self.nvml.close()

    @property
    def rss_delta_mb(self) -> float:
        """Returns peak host RAM delta in megabytes."""
        return max(0.0, self.peak_rss_mb - self.baseline_rss_mb)

    @property
    def vram_delta_mb(self) -> float:
        """Returns peak GPU VRAM delta in megabytes."""
        return max(0.0, self.peak_vram_mb - self.baseline_vram_mb)

    @property
    def scope(self) -> str:
        """Describes whether memory is UMA unified, discrete VRAM, or host RAM."""
        if self.is_uma:
            return "uma-unified"
        if self.vram_delta_mb > 10.0:
            return "discrete-vram"
        return "host-only"
