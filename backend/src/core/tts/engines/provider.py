"""Hardware and runtime execution provider detection (CPU vs CUDA)."""

import ctypes
import functools
import os
import shutil
import sys
from pathlib import Path

__all__ = [
    "CUDA_CACHE_MAX_SIZE",
    "PROVIDER_AUTO",
    "PROVIDER_CPU",
    "PROVIDER_CUDA",
    "is_cuda_available",
    "resolve_execution_provider",
]

CUDA_CACHE_MAX_SIZE: int = 1
PROVIDER_CUDA: str = "cuda"
PROVIDER_CPU: str = "cpu"
PROVIDER_AUTO: str = "auto"


@functools.lru_cache(maxsize=CUDA_CACHE_MAX_SIZE)
def is_cuda_available() -> bool:
    """Returns True if host hardware and installed runtime support CUDA."""
    has_nvidia_hardware = bool(
        shutil.which("nvidia-smi")
        or Path("/dev/nvhost-ctrl").exists()
        or Path("/etc/nv_tegra_release").exists()
        or os.environ.get("CUDA_VISIBLE_DEVICES")
    )
    if not has_nvidia_hardware:
        return False

    try:
        import sherpa_onnx

        file_attr = getattr(sherpa_onnx, "__file__", None)
        if not file_attr:
            return False
        runtime_lib = Path(file_attr).parent / "lib"
        cuda_libs = [
            f for f in runtime_lib.glob("*cuda*") if f.suffix in (".dll", ".so")
        ]
        if not cuda_libs:
            return False

        loader = (
            getattr(ctypes, "WinDLL", ctypes.CDLL)
            if sys.platform == "win32"
            else ctypes.CDLL
        )
        for lib in cuda_libs:
            try:
                loader(str(lib))
                return True
            except OSError:
                continue
        return False
    except (ImportError, OSError, AttributeError):
        return False


def resolve_execution_provider(configured: str) -> str:
    """Resolves 'auto', 'cuda', or 'cpu' to an actual execution provider."""
    normalized = configured.strip().lower()
    if normalized == PROVIDER_CUDA:
        return PROVIDER_CUDA
    if normalized == PROVIDER_CPU:
        return PROVIDER_CPU
    return PROVIDER_CUDA if is_cuda_available() else PROVIDER_CPU
