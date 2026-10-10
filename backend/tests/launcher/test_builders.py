"""Unit tests for the launcher build and provisioning steps (builders.py)."""

import os
import subprocess
from unittest.mock import patch

from tools.launcher import builders, paths


def _finished(return_code):
    """Builds a finished subprocess result with the given exit code."""
    return subprocess.CompletedProcess(args=[], returncode=return_code)


def _clear_pwa_static_dir(monkeypatch):
    """Clears PWA_STATIC_DIR via monkeypatch so build_pwa's setdefault is undone."""
    monkeypatch.setenv("PWA_STATIC_DIR", "placeholder")
    monkeypatch.delenv("PWA_STATIC_DIR")


def test_build_pwa_no_package_json():
    """Verifies build_pwa aborts early if pwa/app/package.json is missing."""
    with patch("pathlib.Path.is_file", return_value=False):
        assert builders.build_pwa() is False


def test_build_pwa_no_pnpm_with_prebuilt_bundle(capsys, monkeypatch):
    """Verifies fallback to prebuilt PWA bundle when pnpm is absent."""
    _clear_pwa_static_dir(monkeypatch)

    def fake_is_file(self):
        return self.name in ("package.json", "index.html")

    with (
        patch("pathlib.Path.is_file", side_effect=fake_is_file, autospec=True),
        patch("tools.launcher.builders.resolve_pnpm", return_value=None),
    ):
        success = builders.build_pwa()
        assert success is True
        assert "PWA_STATIC_DIR" in os.environ
        captured = capsys.readouterr().out
        assert "using existing pre-built bundle" in captured


def test_build_pwa_no_pnpm_no_prebuilt_bundle(capsys):
    """Verifies warning and failure when pnpm is missing and no prebuilt dist exists."""

    def fake_is_file(self):
        return self.name == "package.json"

    with (
        patch("pathlib.Path.is_file", side_effect=fake_is_file, autospec=True),
        patch("tools.launcher.builders.resolve_pnpm", return_value=None),
    ):
        success = builders.build_pwa()
        assert success is False
        captured = capsys.readouterr().out
        assert "pnpm not found and no pre-built bundle exists" in captured


def test_build_pwa_installs_dependencies_and_builds(monkeypatch):
    """Verifies pnpm install is executed if node_modules is missing, then build."""
    _clear_pwa_static_dir(monkeypatch)

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=False),
        patch("tools.launcher.builders.resolve_pnpm", return_value="/bin/pnpm"),
        patch("subprocess.run", return_value=_finished(0)) as mock_sub,
    ):
        assert builders.build_pwa() is True
        assert mock_sub.call_count == 2
        assert mock_sub.call_args_list[0][0][0] == ["/bin/pnpm", "install"]
        assert mock_sub.call_args_list[1][0][0] == ["/bin/pnpm", "run", "build"]


def test_build_pwa_compilation_failure():
    """Verifies build_pwa handles compilation failure return codes cleanly."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=True),
        patch("tools.launcher.builders.resolve_pnpm", return_value="/bin/pnpm"),
        patch("subprocess.run", return_value=_finished(1)),
    ):
        assert builders.build_pwa() is False


def test_build_pwa_install_failure_stops_after_one_command(capsys):
    """Verifies a failed pnpm install returns False after one command and reports it."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=False),
        patch("tools.launcher.builders.resolve_pnpm", return_value="/bin/pnpm"),
        patch("subprocess.run", return_value=_finished(1)) as mock_sub,
    ):
        assert builders.build_pwa() is False
    assert mock_sub.call_count == 1
    assert "'pnpm install' failed" in capsys.readouterr().out


def test_build_pwa_uses_explicit_pnpm_binary(monkeypatch):
    """Verifies an explicit pnpm_bin is used and resolve_pnpm is never consulted."""
    _clear_pwa_static_dir(monkeypatch)

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=False),
        patch("tools.launcher.builders.resolve_pnpm") as mock_resolve,
        patch("subprocess.run", return_value=_finished(0)) as mock_sub,
    ):
        assert builders.build_pwa(pnpm_bin="/explicit/pnpm") is True
    mock_resolve.assert_not_called()
    assert mock_sub.call_args_list[0][0][0][0] == "/explicit/pnpm"


def test_build_pwa_skips_install_when_node_modules_exists(monkeypatch):
    """Verifies a present node_modules skips pnpm install and runs only the build."""
    _clear_pwa_static_dir(monkeypatch)

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=True),
        patch("tools.launcher.builders.resolve_pnpm", return_value="/bin/pnpm"),
        patch("subprocess.run", return_value=_finished(0)) as mock_sub,
    ):
        assert builders.build_pwa() is True
    mock_sub.assert_called_once()
    assert mock_sub.call_args[0][0] == ["/bin/pnpm", "run", "build"]


def test_build_pwa_success_sets_pwa_static_dir(monkeypatch):
    """Verifies a successful build points PWA_STATIC_DIR at the compiled dist."""
    _clear_pwa_static_dir(monkeypatch)

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=True),
        patch("tools.launcher.builders.resolve_pnpm", return_value="/bin/pnpm"),
        patch("subprocess.run", return_value=_finished(0)),
    ):
        assert builders.build_pwa() is True
    assert os.environ["PWA_STATIC_DIR"] == str(paths.PWA_DIST_DIR)


def test_build_llama_success_and_force():
    """Verifies build_llama runs the llama-tts-daemon build script with --force."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("subprocess.run", return_value=_finished(0)) as mock_run,
    ):
        assert builders.build_llama(force=True) is True
        assert mock_run.call_count == 1
        assert "--force" in mock_run.call_args[0][0]


def test_build_llama_without_force_omits_force_flag():
    """Verifies build_llama without force omits --force and passes the interpreter."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("subprocess.run", return_value=_finished(0)) as mock_run,
    ):
        assert builders.build_llama(python_bin="/mock/python") is True
    assert mock_run.call_args[0][0] == ["/mock/python", str(paths.LLAMA_BUILD_SCRIPT)]


def test_build_llama_returns_false_when_script_exits_nonzero():
    """Verifies build_llama returns False when the build script exits non-zero."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("subprocess.run", return_value=_finished(1)),
    ):
        assert builders.build_llama(python_bin="/mock/python") is False


def test_build_llama_missing_script():
    """Verifies build_llama returns False when build script is missing."""
    with patch("pathlib.Path.is_file", return_value=False):
        assert builders.build_llama() is False


def test_sync_backend_success():
    """Verifies sync_backend executes uv sync --all-extras on backend directory."""
    with patch("subprocess.run", return_value=_finished(0)) as mock_sub:
        assert builders.sync_backend("/mock/bin/uv") is True
        assert mock_sub.call_count == 1
        cmd = mock_sub.call_args[0][0]
        assert cmd[:3] == ["/mock/bin/uv", "sync", "--all-extras"]
        assert "--directory" in cmd
        assert "backend" in str(cmd[cmd.index("--directory") + 1])


def test_sync_backend_without_argument_uses_resolve_uv():
    """Verifies sync_backend falls back to resolve_uv when no uv command is given."""
    with (
        patch("tools.launcher.builders.resolve_uv", return_value="/mock/uv"),
        patch("subprocess.run", return_value=_finished(0)) as mock_sub,
    ):
        assert builders.sync_backend() is True
    assert mock_sub.call_args[0][0][0] == "/mock/uv"


def test_sync_backend_failure():
    """Verifies sync_backend returns False when uv sync exits with non-zero code."""
    with patch("subprocess.run", return_value=_finished(1)):
        assert builders.sync_backend("/mock/bin/uv") is False


def test_download_models_success_runs_script_for_target():
    """Verifies download_models runs the script for the target from the repo root."""
    with patch("subprocess.run", return_value=_finished(0)) as mock_sub:
        assert builders.download_models("minimal", python_bin="/mock/python") is True
    assert mock_sub.call_count == 1
    assert mock_sub.call_args[0][0] == [
        "/mock/python",
        str(paths.DOWNLOAD_MODELS_SCRIPT),
        "--target",
        "minimal",
    ]
    assert mock_sub.call_args.kwargs["cwd"] == str(paths.ROOT_DIR)


def test_download_models_returns_false_on_nonzero_exit():
    """Verifies download_models returns False when the download script fails."""
    with patch("subprocess.run", return_value=_finished(1)):
        assert builders.download_models("all", python_bin="/mock/python") is False


def test_download_models_without_python_bin_uses_resolve_python():
    """Verifies download_models falls back to resolve_python without python_bin."""
    with (
        patch(
            "tools.launcher.builders.resolve_python",
            return_value="/mock/resolved-python",
        ) as mock_resolve,
        patch("subprocess.run", return_value=_finished(0)) as mock_sub,
    ):
        assert builders.download_models("minimal") is True
    mock_resolve.assert_called_once()
    assert mock_sub.call_args[0][0][0] == "/mock/resolved-python"
