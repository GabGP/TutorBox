"""Returns the backend's freed heap to the operating system, not only to its own allocator."""

import ctypes
import gc
import sys

from core.system_health.release_report import ReleaseAction

__all__ = ["trim_backend_heap"]

HEAP_TARGET = "heap del proceso"
GLIBC_LIBRARY = "libc.so.6"


def trim_backend_heap() -> ReleaseAction:
    """Collects garbage, then asks glibc to give the unused heap pages back (Linux only)."""
    gc.collect()
    if not sys.platform.startswith("linux"):
        return ReleaseAction(
            target=HEAP_TARGET,
            kind="backend_heap",
            action="unsupported",
            detail="malloc_trim needs Linux with glibc; only the garbage collector ran",
        )
    try:
        released = ctypes.CDLL(GLIBC_LIBRARY).malloc_trim(0)
    except (OSError, AttributeError) as error:
        return ReleaseAction(
            target=HEAP_TARGET,
            kind="backend_heap",
            action="failed",
            detail=f"malloc_trim unavailable: {error}",
        )
    return ReleaseAction(
        target=HEAP_TARGET,
        kind="backend_heap",
        action="unloaded",
        detail="malloc_trim returned free pages"
        if released
        else "no free pages to return",
    )
