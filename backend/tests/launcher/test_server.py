"""Unit tests for the Utz'tutor launcher Uvicorn command assembly and launch."""

from unittest.mock import patch

from tools.launcher import console, paths, server


def _values_after_flag(cmd, flag):
    """Returns every token that directly follows the given flag in a command."""
    return [cmd[index + 1] for index, token in enumerate(cmd) if token == flag]


def test_build_uvicorn_command_starts_with_uv_run_prefix():
    """Verifies the command runs uvicorn main:app via uv with host and port."""
    cmd = server.build_uvicorn_command("uv", host="0.0.0.0", port=8123, reload=False)

    assert cmd[:6] == [
        "uv",
        "run",
        "--directory",
        str(paths.BACKEND_DIR),
        "uvicorn",
        "main:app",
    ]
    assert _values_after_flag(cmd, "--host") == ["0.0.0.0"]
    assert _values_after_flag(cmd, "--port") == ["8123"]


def test_build_uvicorn_command_with_reload_watches_src_and_migrations():
    """Verifies reload mode adds --reload with exactly two reload directories."""
    cmd = server.build_uvicorn_command("uv", host="127.0.0.1", port=8000, reload=True)

    assert "--reload" in cmd
    assert _values_after_flag(cmd, "--reload-dir") == [
        str(paths.BACKEND_DIR / "src"),
        str(paths.BACKEND_DIR / "migrations"),
    ]


def test_build_uvicorn_command_without_reload_has_no_reload_flags():
    """Verifies disabled reload omits both --reload and --reload-dir."""
    cmd = server.build_uvicorn_command("uv", host="127.0.0.1", port=8000, reload=False)

    assert "--reload" not in cmd
    assert "--reload-dir" not in cmd


def test_build_uvicorn_command_includes_log_config_when_file_exists():
    """Verifies --log-config points at logging_config.json when that file exists."""
    with patch("pathlib.Path.is_file", return_value=True):
        cmd = server.build_uvicorn_command(
            "uv", host="127.0.0.1", port=8000, reload=False
        )

    assert "--log-config" in cmd
    assert cmd[cmd.index("--log-config") + 1].endswith("logging_config.json")


def test_build_uvicorn_command_omits_log_config_when_file_missing():
    """Verifies --log-config is left out when logging_config.json is absent."""
    with patch("pathlib.Path.is_file", return_value=False):
        cmd = server.build_uvicorn_command(
            "uv", host="127.0.0.1", port=8000, reload=False
        )

    assert "--log-config" not in cmd


def test_print_client_urls_lists_classroom_and_docs_urls_then_banner(capsys):
    """Verifies print_client_urls prints the client URLs and ends with the banner."""
    server.print_client_urls(8123)

    expected_lines = [
        "Classroom Client URLs:",
        "  * Maestro (Teacher) : http://localhost:8123/maestro/",
        "  * Alumno (Student)  : http://localhost:8123/alumno/",
        "  * Pantalla (Screen) : http://localhost:8123/pantalla/",
        "  * API Docs (Swagger): http://localhost:8123/docs",
        console.BANNER_LINE,
    ]
    assert capsys.readouterr().out.splitlines() == expected_lines


def test_serve_runs_uvicorn_once_from_root_directory(capsys):
    """Verifies serve runs the built command once from ROOT_DIR and logs it."""
    with patch("subprocess.run") as run_mock:
        server.serve("uv", host="127.0.0.1", port=8000, reload=False)

    assert run_mock.call_count == 1
    expected_cmd = server.build_uvicorn_command(
        "uv", host="127.0.0.1", port=8000, reload=False
    )
    assert run_mock.call_args[0][0] == expected_cmd
    assert run_mock.call_args.kwargs["cwd"] == str(paths.ROOT_DIR)
    assert run_mock.call_args.kwargs["check"] is False
    printed_lines = capsys.readouterr().out.splitlines()
    assert any(line.startswith("Running: ") for line in printed_lines)


def test_serve_swallows_keyboard_interrupt_and_reports_stop(capsys):
    """Verifies serve catches KeyboardInterrupt and prints the stop message."""
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        server.serve("uv", host="127.0.0.1", port=8000, reload=False)

    assert "Utz'tutor server stopped." in capsys.readouterr().out
