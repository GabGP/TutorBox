"""Environment variable file discovery and loader for TutorBox appliance."""

import os
from pathlib import Path

from config.constants import PROJECT_ROOT


def load_env_file(custom_path: Path | None = None) -> None:
    """Loads environment variables from root or backend .env file if present."""
    if custom_path is not None:
        search_paths = [custom_path]
    else:
        search_paths = [
            PROJECT_ROOT / ".env",
            PROJECT_ROOT / "backend" / ".env",
        ]
    for env_path in search_paths:
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, val = stripped.split("=", 1)
                clean_key, clean_val = key.strip(), val.strip().strip("'\"")
                if clean_key and clean_key not in os.environ:
                    os.environ[clean_key] = clean_val
            break
