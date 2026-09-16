"""Hardware and runtime execution provider detection (CPU vs CUDA)."""

import ctypes
import functools
import os
import shutil
import sys
from pathlib import Path

__all__ = ["is_cuda_available", "resolve_execution_provider"]


@functools.lru_cache(maxsize=1)
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

        loader = ctypes.WinDLL if sys.platform == "win32" else ctypes.CDLL
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
    if normalized == "cuda":
        return "cuda"
    if normalized == "cpu":
        return "cpu"
    return "cuda" if is_cuda_available() else "cpu"
