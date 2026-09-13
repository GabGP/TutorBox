#!/usr/bin/env python3
"""TutorBox Appliance & Development Runner.

Checks runtime prerequisites (uv, espeak-ng, local llama-server) and boots
the TutorBox FastAPI backend & Pilas classroom web clients.
"""

import argparse
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"


def check_prerequisites() -> None:
    # 1. espeak-ng check
    tts_bin = shutil.which("espeak-ng") or shutil.which("espeak")
    if not tts_bin:
        print(
            "[\033[33mWARN\033[0m] espeak-ng not found. Spoken voice (>51% distractor rule) will be unavailable."
        )
        print("       Install on Ubuntu/Debian: sudo apt install espeak-ng")
    else:
        print(f"[\033[32mOK\033[0m] Found TTS engine: {tts_bin}")

    # 2. llama.cpp / SLM check
    slm_url = os.getenv("SLM_BASE_URL", "http://127.0.0.1:8080/v1")
    try:
        req = urllib.request.Request(f"{slm_url.rstrip('/')}/models", method="GET")
        with urllib.request.urlopen(req, timeout=1.5):
            print(f"[\033[32mOK\033[0m] Local SLM engine reachable at {slm_url}")
    except (urllib.error.URLError, TimeoutError, OSError):
        print(
            f"[\033[33mINFO\033[0m] SLM engine not detected at {slm_url}. Dynamic quiz generation requires llama-server."
        )
        print("       (Seed question bank will still work seamlessly offline.)")


def resolve_uv() -> str:
    found = shutil.which("uv")
    if found:
        return found
    for fallback in [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
    ]:
        if fallback.is_file() and os.access(fallback, os.X_OK):
            return str(fallback)
    return "uv"


def load_env(env_path: Path) -> None:
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, val = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def main() -> None:
    load_env(ROOT_DIR / ".env")
    cache_venv = ROOT_DIR / ".cache" / "venv"
    os.environ.setdefault("UV_PROJECT_ENVIRONMENT", str(cache_venv))

    parser = argparse.ArgumentParser(
        description="TutorBox Appliance Dev & Production Launcher"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--no-reload", action="store_true", help="Disable auto-reloading"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Check prerequisites and exit"
    )
    args = parser.parse_args()

    print("==================================================")
    print("      Starting TutorBox Edge AI Appliance         ")
    print("==================================================")
    check_prerequisites()
    print("--------------------------------------------------")

    if args.check_only:
        return

    uv_cmd = resolve_uv()
    cmd = [
        uv_cmd,
        "run",
        "--directory",
        str(BACKEND_DIR),
        "uvicorn",
        "src.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if not args.no_reload:
        cmd.append("--reload")

    print(f"Running: {' '.join(cmd)}")
    print("Classroom Client URLs:")
    print(f"  * Maestro (Teacher) : http://localhost:{args.port}/maestro/")
    print(f"  * Alumno (Student)  : http://localhost:{args.port}/alumno/")
    print(f"  * Pantalla (Screen) : http://localhost:{args.port}/pantalla/")
    print(f"  * API Docs (Swagger): http://localhost:{args.port}/docs")
    print("==================================================")

    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    except KeyboardInterrupt:
        print("\nTutorBox server stopped.")


if __name__ == "__main__":
    main()
