"""Filesystem locations shared by the Utz'tutor launcher modules."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
PWA_APP_DIR = ROOT_DIR / "pwa" / "app"
PWA_DIST_DIR = ROOT_DIR / ".cache" / "pwa" / "dist"
DEFAULT_VENV_DIR = ROOT_DIR / ".cache" / "venv"
TTS_MODELS_DIR = ROOT_DIR / ".cache" / "models" / "tts"
LLAMA_DAEMON_CACHE_DIR = ROOT_DIR / ".cache" / "bin" / "llama.cpp"
LLAMA_BUILD_SCRIPT = ROOT_DIR / "tools" / "llama-tts-daemon" / "build.py"
DOWNLOAD_MODELS_SCRIPT = ROOT_DIR / "tools" / "voice_models" / "download_models.py"
