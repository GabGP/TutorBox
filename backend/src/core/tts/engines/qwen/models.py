"""Filesystem path, binary, and device resolution for Qwen3-TTS."""

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.config import PROJECT_ROOT, get_settings
from core.tts.exceptions import TTSUnavailableError

__all__ = ["QwenModelPaths", "detect_qwen_provider", "resolve_qwen_paths"]


@dataclass(frozen=True)
class QwenModelPaths:
    """Resolved paths for Qwen3-TTS GGUF weights and llama-tts binary."""

    model_path: Path
    mmproj_path: Path
    bin_path: Path


def _find_qwen_file(configured_path: str, filename: str) -> Path | None:
    configured = Path(configured_path).expanduser() if configured_path else None
    candidate_paths: list[Path] = []
    if configured:
        candidate_paths.extend((configured, configured / filename))
        for candidate in candidate_paths:
            if candidate.is_file():
                return candidate.resolve()
        return None
    candidate_paths.extend(
        (
            PROJECT_ROOT / ".cache" / "models" / "tts" / "qwen" / filename,
            Path.cwd() / ".cache" / "models" / "tts" / "qwen" / filename,
            Path.cwd() / "models" / "tts" / "qwen" / filename,
            Path(get_settings().tts.piper_model_dir) / "qwen" / filename,
        )
    )
    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _find_llama_bin(
    model_dir: Path | None = None, configured_path: str = ""
) -> Path | None:
    bin_name = "llama-tts.exe" if platform.system() == "Windows" else "llama-tts"
    candidate_bins: list[Path] = []
    if configured_path:
        configured = Path(configured_path).expanduser()
        candidate_bins.extend((configured, configured / bin_name))
    if model_dir:
        for ancestor in model_dir.parents:
            candidate_bins.append(ancestor / "bin" / "llama" / bin_name)
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        candidate_roots = [
            Path("C:/Program Files/llama.cpp"),
            Path("C:/Program Files/llama"),
            Path("C:/ProgramData/chocolatey/bin"),
            Path.home() / "AppData/Local/Programs/llama.cpp",
            Path.home() / "scoop/apps/llama.cpp/current",
        ]
        if local_app_data:
            candidate_roots.append(Path(local_app_data) / "llama.cpp")
        for root in candidate_roots:
            candidate_bins.extend((root / bin_name, root / "bin" / bin_name))
    else:
        for root in (
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path.home() / ".local/bin",
            Path("/opt/llama.cpp/bin"),
        ):
            candidate_bins.append(root / bin_name)
    for b in candidate_bins:
        if b.is_file():
            return b.resolve()
    resolved = shutil.which(bin_name)
    return Path(resolved).resolve() if resolved else None


def resolve_qwen_paths(model_path_str: str | None = None) -> QwenModelPaths:
    """Resolves filesystem paths for Qwen3-TTS weights and llama-tts binary."""
    tts = get_settings().tts
    path_to_use = model_path_str or tts.qwen_gguf_path

    model_file = _find_qwen_file(path_to_use, "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf")
    if not model_file:
        raise TTSUnavailableError(
            f"Qwen GGUF model not found (configured: '{path_to_use}')."
        )

    mmproj_file = model_file.parent / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    if not mmproj_file.is_file():
        raise TTSUnavailableError(f"Qwen mmproj not found at '{mmproj_file}'.")

    bin_file = _find_llama_bin(model_file.parent, tts.qwen_binary)
    if not bin_file:
        bin_name = "llama-tts.exe" if platform.system() == "Windows" else "llama-tts"
        raise TTSUnavailableError(f"Binary '{bin_name}' not found on host.")

    return QwenModelPaths(
        model_path=model_file,
        mmproj_path=mmproj_file,
        bin_path=bin_file,
    )


def detect_qwen_provider(paths: QwenModelPaths | None = None) -> str:
    """Reports CUDA when llama-tts exposes a CUDA device, otherwise CPU."""
    try:
        active_paths = paths or resolve_qwen_paths()
        result = subprocess.run(
            [str(active_paths.bin_path), "--list-devices"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, TTSUnavailableError):
        return "cpu"
    devices = f"{result.stdout}\n{result.stderr}".upper()
    return "cuda" if "CUDA" in devices else "cpu"
