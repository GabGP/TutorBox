"""Filesystem locations used by the llama-tts daemon build.

Other modules read these as attributes (paths.SOURCE_DIR) instead of importing
the names, so tests can redirect the whole build to a temporary directory.
"""

from pathlib import Path

DAEMON_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = DAEMON_DIR.parents[1]
SOURCE_DIR = ROOT_DIR / ".cache" / "build" / "llama.cpp"
BUILD_DIR = SOURCE_DIR / "build"
# Applied in this order onto the upstream checkout.
PATCH_FILES = (
    DAEMON_DIR / "0001-llama-tts-daemon-mode.patch",
    DAEMON_DIR / "0002-qwen-tok-embd-rows.patch",
)
CACHE_BIN_DIR = ROOT_DIR / ".cache" / "bin" / "llama.cpp"
LICENSE_SRC = DAEMON_DIR / "LICENSE-llama-cpp"
PROJECT_VENV_DIR = ROOT_DIR / ".cache" / "venv"
