"""Host RAM resident set size from psutil, with a Windows working-set fallback."""

from __future__ import annotations

import sys

from tools.benchmark.tts.memory.windows_rss import working_set_megabytes
from tools.benchmark.tts.shared.units import BYTES_PER_MB


def _psutil_rss_megabytes(include_children: bool) -> float | None:
    """Returns process RSS in MB via psutil, or None when psutil is unusable."""
    try:
        # psutil is optional: it may be missing, or known only through bundled stubs.
        import psutil  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

        process = psutil.Process()
        total_rss = process.memory_info().rss
        if include_children:
            try:
                for child in process.children(recursive=True):
                    total_rss += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return float(total_rss) / BYTES_PER_MB
    except (ImportError, AttributeError):
        return None


def get_host_rss_mb(include_children: bool = True) -> float:
    """Returns host RAM resident set size in MB for process and its children."""
    psutil_megabytes = _psutil_rss_megabytes(include_children)
    if psutil_megabytes is not None:
        return psutil_megabytes
    if sys.platform == "win32":
        windows_megabytes = working_set_megabytes()
        if windows_megabytes is not None:
            return windows_megabytes
    return 0.0
