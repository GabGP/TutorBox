"""Windows working-set size of this process, read through psapi."""

from __future__ import annotations

import ctypes

from tools.benchmark.tts.shared.units import BYTES_PER_MB


def working_set_megabytes() -> float | None:
    """Returns this process's working set in MB, or None if the Windows call fails."""
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

        get_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        get_memory_info.restype = wintypes.BOOL
        memory_counters = PROCESS_MEMORY_COUNTERS_EX()
        memory_counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
        if get_memory_info(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(memory_counters),
            memory_counters.cb,
        ):
            return float(memory_counters.WorkingSetSize) / BYTES_PER_MB
    except Exception:  # noqa: BLE001, S110
        # The Windows API is optional here: any failure means "no working set value".
        pass
    return None
