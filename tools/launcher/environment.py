"""Environment file loading and virtualenv location for the Utz'tutor launcher."""

import os
from pathlib import Path

from tools.launcher.paths import DEFAULT_VENV_DIR, ROOT_DIR


def load_env(env_path: Path) -> None:
    """Loads key-value pairs from an env file into os.environ if not already defined."""
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, val = stripped.split("=", 1)
            clean_key = key.strip()
            clean_val = val.strip().strip("'\"")
            if clean_key and clean_key not in os.environ:
                os.environ[clean_key] = clean_val


def resolve_venv_path() -> Path:
    """Returns the absolute virtualenv directory (UV_PROJECT_ENVIRONMENT or .cache/venv)."""
    raw_venv = os.environ.get("UV_PROJECT_ENVIRONMENT")
    venv_path = Path(raw_venv) if raw_venv else DEFAULT_VENV_DIR
    if not venv_path.is_absolute():
        venv_path = (ROOT_DIR / venv_path).resolve()
    return venv_path
