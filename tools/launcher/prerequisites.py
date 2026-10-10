"""Runtime prerequisite checks reported by the Utz'tutor launcher at startup."""

import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from tools.launcher.console import TAG_INFO, TAG_OK, TAG_WARN
from tools.launcher.paths import TTS_MODELS_DIR
from tools.launcher.resolvers import resolve_llama_daemon, resolve_pnpm


def check_voice_models(models_dir: Path | None = None) -> list[str]:
    """Returns a list of missing neural voice engine names in the models directory."""
    target_dir = models_dir or TTS_MODELS_DIR
    piper_ok = (target_dir / "es_ES-sharvard-medium.onnx").is_file()
    kokoro_ok = (target_dir / "kokoro-int8-multi-lang-v1_0" / "voices.bin").is_file()
    qwen_ok = (
        target_dir / "qwen" / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    ).is_file() and (
        target_dir / "qwen" / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    ).is_file()

    missing: list[str] = []
    if not piper_ok:
        missing.append("Piper/Sherpa")
    if not kokoro_ok:
        missing.append("Kokoro-82M")
    if not qwen_ok:
        missing.append("Qwen3-TTS")
    return missing


def _check_espeak() -> None:
    """Reports whether the espeak-ng TTS engine is installed or the custom binary resolves."""
    tts_custom = os.getenv("TTS_ESPEAK_BINARY", "").strip()
    tts_bin = (
        shutil.which(tts_custom)
        if tts_custom
        else (shutil.which("espeak-ng") or shutil.which("espeak"))
    )
    if not tts_bin:
        print(
            f"{TAG_WARN} espeak-ng not found. Spoken voice (>51% distractor rule) will be unavailable."
        )
        print("       Install on Ubuntu/Debian: sudo apt install espeak-ng")
    else:
        print(f"{TAG_OK} Found TTS engine: {tts_bin}")


def _check_slm() -> None:
    """Reports whether the local SLM server answers on its models endpoint."""
    slm_url = os.getenv("SLM_BASE_URL", "http://127.0.0.1:8080/v1")
    try:
        req = urllib.request.Request(f"{slm_url.rstrip('/')}/models", method="GET")
        with urllib.request.urlopen(req, timeout=1.5):
            print(f"{TAG_OK} Local SLM engine reachable at {slm_url}")
    except (urllib.error.URLError, TimeoutError, OSError):
        print(
            f"{TAG_INFO} SLM engine not detected at {slm_url}. Dynamic quiz generation requires llama-server."
        )
        print("       (Seed question bank will still work seamlessly offline.)")


def _check_llama_daemon() -> None:
    """Reports whether the Qwen3-TTS llama-tts daemon binary is available."""
    daemon_bin = resolve_llama_daemon()
    if daemon_bin:
        print(f"{TAG_OK} Found Qwen3-TTS daemon: {daemon_bin}")
    else:
        print(
            f"{TAG_INFO} Qwen3-TTS daemon not found. Run 'python tools/llama_tts_daemon/build.py' or '--build-llama' to compile."
        )


def _check_pnpm() -> None:
    """Reports whether the pnpm package manager is available for the frontend build."""
    pnpm_bin = resolve_pnpm()
    if not pnpm_bin:
        print(
            f"{TAG_WARN} pnpm not found. Frontend PWA auto-compilation will be unavailable."
        )
        print(
            "       Install via: npm install -g pnpm  or  curl -fsSL https://get.pnpm.io/install.sh | sh"
        )
    else:
        print(f"{TAG_OK} Found frontend package manager: {pnpm_bin}")


def _check_voice_models_present() -> None:
    """Reports whether every neural voice model is present in the default models directory."""
    missing_models = check_voice_models()
    if missing_models:
        print(f"{TAG_WARN} Missing neural voice models: {', '.join(missing_models)}.")
        print(
            "       Spoken feedback (>51% rule) will fall back to available engines or eSpeak-ng."
        )
        print(
            "       To download models: ./run.py --download-models [all|qwen|kokoro|minimal]"
        )
    else:
        print(
            f"{TAG_OK} Found all neural voice models (Piper/Sherpa, Kokoro, Qwen3-TTS)"
        )


def check_prerequisites() -> None:
    """Verifies runtime dependencies (espeak-ng, SLM server, Qwen daemon, and pnpm).

    Logs informative warning messages if optional runtime engines are not reachable.
    """
    _check_espeak()
    _check_slm()
    _check_llama_daemon()
    _check_pnpm()
    _check_voice_models_present()
