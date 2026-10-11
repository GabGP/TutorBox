#!/usr/bin/env python3
"""Utz'tutor Appliance & Development Runner.

Checks runtime prerequisites (uv, espeak-ng, local llama-server, pnpm) and boots
the Utz'tutor FastAPI backend & classroom web clients. The steps themselves live
in tools/launcher/; this file only orders them.
"""

import os
import sys
from pathlib import Path

# Centralize ALL bytecode caches under .cache (repo policy).
# NOTE: for run.py's own __pycache__, PYTHONPYCACHEPREFIX must already be
# exported in the shell before `python run.py` starts (see .env.example §9).
# This setdefault covers the uvicorn subprocess; sys.pycache_prefix covers the
# tools.launcher imports below, which is why they come after this block.
_PYCACHE_DIR = Path(__file__).resolve().parent / ".cache" / "pycache"
try:
    _PYCACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
os.environ.setdefault("PYTHONPYCACHEPREFIX", str(_PYCACHE_DIR))
if getattr(sys, "pycache_prefix", None) is None:
    try:
        sys.pycache_prefix = str(_PYCACHE_DIR)
    except (AttributeError, TypeError, ValueError):
        pass

from tools.launcher.builders import (
    build_llama,
    build_pwa,
    download_models,
    sync_backend,
)
from tools.launcher.cli import parse_arguments
from tools.launcher.console import (
    TAG_BUILD,
    TAG_FAIL,
    print_banner,
    print_separator,
)
from tools.launcher.environment import load_env, resolve_venv_path
from tools.launcher.paths import BACKEND_DIR, ROOT_DIR
from tools.launcher.prerequisites import check_prerequisites
from tools.launcher.resolvers import resolve_python, resolve_uv
from tools.launcher.server import serve


def main() -> None:
    """Boots the Utz'tutor appliance development server and launches Uvicorn."""
    load_env(ROOT_DIR / ".env")
    load_env(BACKEND_DIR / ".env")
    os.environ["UV_PROJECT_ENVIRONMENT"] = str(resolve_venv_path())
    args = parse_arguments()

    print_banner()
    check_prerequisites()
    print_separator()

    if args.check_only and not (
        args.build_llama or args.force_build_llama or args.download_models
    ):
        return

    uv_cmd = resolve_uv()
    if not args.no_sync:
        if not sync_backend(uv_cmd):
            sys.exit(1)
        print_separator()

    py_bin = resolve_python()

    if args.download_models:
        print(
            f"{TAG_BUILD} Downloading voice models (target: {args.download_models})..."
        )
        if not download_models(args.download_models, python_bin=py_bin):
            print(f"{TAG_FAIL} Failed to download voice models.")
            sys.exit(1)
        print_separator()

    if args.build_llama or args.force_build_llama:
        print(f"{TAG_BUILD} Building Qwen3-TTS daemon binary...")
        if not build_llama(force=args.force_build_llama, python_bin=py_bin):
            print(f"{TAG_FAIL} Failed to build Qwen3-TTS daemon.")
            sys.exit(1)
        print_separator()

    if args.check_only:
        return

    if not args.no_build:
        build_pwa()
        print_separator()

    serve(uv_cmd, host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
