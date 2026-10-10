"""Uvicorn command assembly and launch for the Utz'tutor launcher."""

import subprocess

from tools.launcher.console import BANNER_LINE
from tools.launcher.paths import BACKEND_DIR, ROOT_DIR


def build_uvicorn_command(
    uv_cmd: str, *, host: str, port: int, reload: bool
) -> list[str]:
    """Builds the `uv run uvicorn` command line for the backend application."""
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
        host,
        "--port",
        str(port),
    ]
    if reload:
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
    return cmd


def print_client_urls(port: int) -> None:
    """Prints the classroom client and API documentation URLs."""
    print("Classroom Client URLs:")
    print(f"  * Maestro (Teacher) : http://localhost:{port}/maestro/")
    print(f"  * Alumno (Student)  : http://localhost:{port}/alumno/")
    print(f"  * Pantalla (Screen) : http://localhost:{port}/pantalla/")
    print(f"  * API Docs (Swagger): http://localhost:{port}/docs")
    print(BANNER_LINE)


def serve(uv_cmd: str, *, host: str, port: int, reload: bool) -> None:
    """Launches Uvicorn and blocks until the server stops."""
    cmd = build_uvicorn_command(uv_cmd, host=host, port=port, reload=reload)
    print(f"Running: {' '.join(cmd)}")
    print_client_urls(port)
    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    except KeyboardInterrupt:
        print("\nUtz'tutor server stopped.")
