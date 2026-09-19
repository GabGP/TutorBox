#!/usr/bin/env python3
"""TutorBox Appliance & Development Runner.

Checks runtime prerequisites (uv, espeak-ng, local llama-server, pnpm) and boots
the TutorBox FastAPI backend & classroom web clients.
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
PWA_APP_DIR = ROOT_DIR / "pwa" / "app"
PWA_DIST_DIR = ROOT_DIR / ".cache" / "pwa" / "dist"

# Centralize ALL bytecode caches under .cache (repo policy).
# NOTE: for run.py's own __pycache__, PYTHONPYCACHEPREFIX must already be
# exported in the shell before `python run.py` starts (see .env.example §9).
# This setdefault covers the uvicorn subprocess; sys.pycache_prefix covers
# any late imports in this process.
_PYCACHE_DIR = ROOT_DIR / ".cache" / "pycache"
try:
    _PYCACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
os.environ.setdefault("PYTHONPYCACHEPREFIX", str(_PYCACHE_DIR))
if getattr(sys, "pycache_prefix", None) is None:
    try:
        sys.pycache_prefix = str(_PYCACHE_DIR)
    except Exception:
        pass

# Console output tags and shared PWA messages (single source of truth for
# user-facing runner output; backend tests assert on the message bodies).
TAG_INFO = "[\033[33mINFO\033[0m]"
TAG_WARN = "[\033[33mWARN\033[0m]"
TAG_FAIL = "[\033[31mFAIL\033[0m]"
TAG_BUILD = "[\033[34mBUILD\033[0m]"
TAG_OK = "[\033[32mOK\033[0m]"

PWA_DIST_LABEL = ".cache/pwa/dist"
PWA_BUILD_CMD = "pnpm --dir pwa/app run build"
LEGACY_CLIENT_ENV = "PWA_STATIC_DIR=pwa/pilas"
MSG_BACKEND_FAIL_FAST = f"Backend default ({PWA_DIST_LABEL}) will fail fast on startup."


def _print_fail_fast_hint() -> None:
    """Shared closing note when the PWA bundle is unavailable."""
    print(f"       {MSG_BACKEND_FAIL_FAST}")
    print(f"       Explicitly set {LEGACY_CLIENT_ENV} for the legacy client.")


def resolve_pnpm() -> str | None:
    """Finds and returns the executable path for the pnpm package manager."""
    found = shutil.which("pnpm")
    if found:
        return found
    for fallback in [
        Path.home() / ".local" / "share" / "pnpm" / "pnpm",
        Path.home() / ".local" / "bin" / "pnpm",
        Path.home() / "AppData" / "Roaming" / "npm" / "pnpm.cmd",
    ]:
        if fallback.is_file() and (os.name == "nt" or os.access(fallback, os.X_OK)):
            return str(fallback)
    return None


def build_pwa(pnpm_bin: str | None = None) -> bool:
    """Compiles the React 19 + TypeScript PWA in pwa/app to .cache/pwa/dist.

    Verifies dependencies, runs the Vite production build, and ensures
    fresh assets are ready before the backend server boots.
    """
    if not (PWA_APP_DIR / "package.json").is_file():
        return False

    resolved_pnpm = pnpm_bin or resolve_pnpm()
    if not resolved_pnpm:
        if (PWA_DIST_DIR / "index.html").is_file():
            print(
                f"{TAG_INFO} pnpm not detected; using existing pre-built bundle in {PWA_DIST_LABEL}."
            )
            os.environ.setdefault("PWA_STATIC_DIR", str(PWA_DIST_DIR))
            return True
        print(
            f"{TAG_WARN} pnpm not found and no pre-built bundle exists in {PWA_DIST_LABEL}."
        )
        print(f"       Install pnpm, then build with ({PWA_BUILD_CMD}).")
        _print_fail_fast_hint()
        return False

    if not (PWA_APP_DIR / "node_modules").is_dir():
        print(f"{TAG_BUILD} Installing frontend dependencies (pnpm install)...")
        install_res = subprocess.run(
            [resolved_pnpm, "install"], cwd=str(PWA_APP_DIR), check=False
        )
        if install_res.returncode != 0:
            print(f"{TAG_FAIL} 'pnpm install' failed. Skipping PWA build.")
            _print_fail_fast_hint()
            return False

    print(f"{TAG_BUILD} Compiling modular PWA frontend (pnpm run build)...")
    build_res = subprocess.run(
        [resolved_pnpm, "run", "build"], cwd=str(PWA_APP_DIR), check=False
    )
    if build_res.returncode != 0:
        print(
            f"{TAG_FAIL} PWA frontend build failed. Check compilation errors above."
        )
        _print_fail_fast_hint()
        return False

    print(f"{TAG_OK} PWA frontend successfully compiled to {PWA_DIST_LABEL}")
    os.environ.setdefault("PWA_STATIC_DIR", str(PWA_DIST_DIR))
    return True


def resolve_llama_daemon() -> Path | None:
    """Finds and returns the path to the llama-tts-daemon binary if available."""
    ext = ".exe" if os.name == "nt" else ""
    bin_name = f"llama-tts-daemon{ext}"
    cached = ROOT_DIR / ".cache" / "bin" / "llama.cpp" / bin_name
    if cached.is_file():
        return cached
    which_daemon = shutil.which(bin_name) or shutil.which(f"llama-tts{ext}")
    return Path(which_daemon).resolve() if which_daemon else None


def build_llama(force: bool = False) -> bool:
    """Invokes tools/llama-tts-daemon/build.py to compile and install the daemon binary."""
    script = ROOT_DIR / "tools" / "llama-tts-daemon" / "build.py"
    if not script.is_file():
        print(f"{TAG_FAIL} Build script not found at {script}")
        return False
    cmd = [sys.executable, str(script)]
    if force:
        cmd.append("--force")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    return res.returncode == 0


def check_prerequisites() -> None:
    """Verifies runtime dependencies (espeak-ng, SLM server, Qwen daemon, and pnpm).

    Logs informative warning messages if optional runtime engines are not reachable.
    """
    # 1. espeak-ng check
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

    # 2. llama.cpp / SLM check
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

    # 3. Qwen3-TTS / llama-tts daemon check
    daemon_bin = resolve_llama_daemon()
    if daemon_bin:
        print(f"{TAG_OK} Found Qwen3-TTS daemon: {daemon_bin}")
    else:
        print(
            f"{TAG_INFO} Qwen3-TTS daemon not found. Run 'python tools/llama-tts-daemon/build.py' or '--build-llama' to compile."
        )

    # 4. pnpm check
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

    # 5. Neural voice models check
    missing_models = check_voice_models()
    if missing_models:
        print(
            f"{TAG_WARN} Missing neural voice models: {', '.join(missing_models)}."
        )
        print(
            "       Spoken feedback (>51% rule) will fall back to available engines or eSpeak-ng."
        )
        print(
            "       To download models: python tools/download_models.py [--target minimal|kokoro|qwen|all]"
        )
    else:
        print(
            f"{TAG_OK} Found all neural voice models (Piper/Sherpa, Kokoro, Qwen3-TTS)"
        )


def check_voice_models(models_dir: Path | None = None) -> list[str]:
    """Returns a list of missing neural voice engine names in the models directory."""
    target_dir = models_dir or (ROOT_DIR / ".cache" / "models" / "tts")
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


def resolve_uv() -> str:
    """Finds and returns the executable path for the uv package manager."""
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


def main() -> None:
    """Boots the TutorBox appliance development server and launches Uvicorn."""
    load_env(ROOT_DIR / ".env")
    load_env(BACKEND_DIR / ".env")
    raw_venv = os.environ.get("UV_PROJECT_ENVIRONMENT")
    venv_path = Path(raw_venv) if raw_venv else ROOT_DIR / ".cache" / "venv"
    if not venv_path.is_absolute():
        venv_path = (ROOT_DIR / venv_path).resolve()
    os.environ["UV_PROJECT_ENVIRONMENT"] = str(venv_path)

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
        "--no-build", action="store_true", help="Skip frontend PWA compilation"
    )
    parser.add_argument(
        "--build-llama",
        action="store_true",
        help="Compile and install patched llama-tts daemon before launching",
    )
    parser.add_argument(
        "--force-build-llama",
        action="store_true",
        help="Force clean re-clone and recompilation of llama-tts daemon",
    )
    parser.add_argument(
        "--download-models",
        nargs="?",
        const="minimal",
        choices=["minimal", "kokoro", "qwen", "all"],
        help="Download voice models before launching (choices: minimal, kokoro, qwen, all; default: minimal)",
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

    if args.download_models:
        print(
            f"{TAG_BUILD} Downloading voice models (target: {args.download_models})..."
        )
        dl_script = ROOT_DIR / "tools" / "download_models.py"
        dl_res = subprocess.run(
            [sys.executable, str(dl_script), "--target", args.download_models],
            cwd=str(ROOT_DIR),
            check=False,
        )
        if dl_res.returncode != 0:
            print(f"{TAG_FAIL} Failed to download voice models.")
            sys.exit(1)
        print("--------------------------------------------------")

    if args.build_llama or args.force_build_llama:
        print(f"{TAG_BUILD} Building Qwen3-TTS daemon binary...")
        if not build_llama(force=args.force_build_llama):
            print(f"{TAG_FAIL} Failed to build Qwen3-TTS daemon.")
            sys.exit(1)
        print("--------------------------------------------------")

    if args.check_only:
        return

    if not args.no_build:
        build_pwa()
        print("--------------------------------------------------")

    uv_cmd = resolve_uv()
    cmd = [
        uv_cmd,
        "run",
        "--directory",
        str(BACKEND_DIR),
        "uvicorn",
        "main:app",
        "--app-dir",
        str(BACKEND_DIR / "src"),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if not args.no_reload:
        cmd.extend(
            [
                "--reload",
                "--reload-dir",
                str(BACKEND_DIR / "src"),
                "--reload-dir",
                str(BACKEND_DIR / "migrations"),
            ]
        )

    log_config_path = BACKEND_DIR / "logging_config.json"
    if log_config_path.is_file():
        cmd.extend(["--log-config", str(log_config_path)])

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
