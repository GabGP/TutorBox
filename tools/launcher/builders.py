"""Build and provisioning steps the Utz'tutor launcher runs before the server boots."""

import os
import subprocess

from tools.launcher.console import (
    PWA_BUILD_CMD,
    PWA_DIST_LABEL,
    TAG_BUILD,
    TAG_FAIL,
    TAG_INFO,
    TAG_OK,
    TAG_WARN,
    print_fail_fast_hint,
)
from tools.launcher.paths import (
    BACKEND_DIR,
    DOWNLOAD_MODELS_SCRIPT,
    LLAMA_BUILD_SCRIPT,
    PWA_APP_DIR,
    PWA_DIST_DIR,
    ROOT_DIR,
)
from tools.launcher.resolvers import resolve_pnpm, resolve_python, resolve_uv


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
        print_fail_fast_hint()
        return False

    if not (PWA_APP_DIR / "node_modules").is_dir():
        print(f"{TAG_BUILD} Installing frontend dependencies (pnpm install)...")
        install_res = subprocess.run(
            [resolved_pnpm, "install"], cwd=str(PWA_APP_DIR), check=False
        )
        if install_res.returncode != 0:
            print(f"{TAG_FAIL} 'pnpm install' failed. Skipping PWA build.")
            print_fail_fast_hint()
            return False

    print(f"{TAG_BUILD} Compiling modular PWA frontend (pnpm run build)...")
    build_res = subprocess.run(
        [resolved_pnpm, "run", "build"], cwd=str(PWA_APP_DIR), check=False
    )
    if build_res.returncode != 0:
        print(f"{TAG_FAIL} PWA frontend build failed. Check compilation errors above.")
        print_fail_fast_hint()
        return False

    print(f"{TAG_OK} PWA frontend successfully compiled to {PWA_DIST_LABEL}")
    os.environ.setdefault("PWA_STATIC_DIR", str(PWA_DIST_DIR))
    return True


def build_llama(force: bool = False, python_bin: str | None = None) -> bool:
    """Invokes tools/llama-tts-daemon/build.py to compile and install the daemon binary."""
    script = LLAMA_BUILD_SCRIPT
    if not script.is_file():
        print(f"{TAG_FAIL} Build script not found at {script}")
        return False
    py_exec = python_bin or resolve_python()
    cmd = [py_exec, str(script)]
    if force:
        cmd.append("--force")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    return res.returncode == 0


def sync_backend(uv_cmd: str | None = None) -> bool:
    """Synchronizes backend dependencies with all extras into the target virtualenv."""
    resolved_uv = uv_cmd or resolve_uv()
    print(f"{TAG_BUILD} Synchronizing backend dependencies (uv sync --all-extras)...")
    res = subprocess.run(
        [resolved_uv, "sync", "--all-extras", "--directory", str(BACKEND_DIR)],
        cwd=str(ROOT_DIR),
        check=False,
    )
    if res.returncode != 0:
        print(f"{TAG_FAIL} Failed to synchronize backend dependencies.")
        return False
    print(f"{TAG_OK} Backend dependencies successfully synchronized.")
    return True


def download_models(target: str, python_bin: str | None = None) -> bool:
    """Invokes tools/download_models.py to fetch the voice models for the given tier."""
    py_exec = python_bin or resolve_python()
    res = subprocess.run(
        [py_exec, str(DOWNLOAD_MODELS_SCRIPT), "--target", target],
        cwd=str(ROOT_DIR),
        check=False,
    )
    return res.returncode == 0
