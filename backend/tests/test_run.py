"""Unit tests for TutorBox appliance runner and prerequisite checks (run.py)."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run


def test_resolve_pnpm_when_found():
    """Verifies resolve_pnpm returns path when pnpm is found in PATH."""
    with patch("shutil.which", return_value="/mock/bin/pnpm"):
        assert run.resolve_pnpm() == "/mock/bin/pnpm"


def test_resolve_pnpm_when_missing():
    """Verifies resolve_pnpm returns None when pnpm cannot be located."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=False),
    ):
        assert run.resolve_pnpm() is None


def test_resolve_uv_when_found():
    """Verifies resolve_uv returns path when uv is found in PATH."""
    with patch("shutil.which", return_value="/mock/bin/uv"):
        assert run.resolve_uv() == "/mock/bin/uv"


def test_resolve_uv_fallback():
    """Verifies resolve_uv checks fallback directories if PATH lookup fails."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.is_file", return_value=True),
        patch("os.access", return_value=True),
    ):
        assert "uv" in run.resolve_uv()


def test_load_env_loads_valid_key_values(tmp_path, monkeypatch):
    """Verifies load_env populates os.environ without overwriting existing keys."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MOCK_KEY_ONE=alpha\n# comment\nMOCK_KEY_TWO='beta'\n", encoding="utf-8"
    )
    monkeypatch.delenv("MOCK_KEY_ONE", raising=False)
    monkeypatch.delenv("MOCK_KEY_TWO", raising=False)

    run.load_env(env_file)
    assert os.environ.get("MOCK_KEY_ONE") == "alpha"
    assert os.environ.get("MOCK_KEY_TWO") == "beta"


def test_check_prerequisites_all_reachable(capsys):
    """Verifies prerequisite output when TTS, SLM, Qwen, and pnpm are all available."""
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = None

    with (
        patch("shutil.which", return_value="/usr/bin/espeak-ng"),
        patch("urllib.request.urlopen", return_value=mock_cm),
        patch("run.resolve_llama_daemon", return_value=Path("/mock/llama-tts-daemon")),
        patch("run.resolve_pnpm", return_value="/usr/bin/pnpm"),
        patch("run.check_voice_models", return_value=[]),
    ):
        run.check_prerequisites()
        captured = capsys.readouterr().out
        assert "Found TTS engine" in captured
        assert "Local SLM engine reachable" in captured
        assert "Found Qwen3-TTS daemon" in captured
        assert "Found frontend package manager" in captured
        assert "Found all neural voice models" in captured


def test_check_prerequisites_all_missing(capsys):
    """Verifies prerequisite warnings when engines are unreachable or missing."""
    with (
        patch("shutil.which", return_value=None),
        patch("urllib.request.urlopen", side_effect=OSError("Unreachable")),
        patch("run.resolve_llama_daemon", return_value=None),
        patch("run.resolve_pnpm", return_value=None),
        patch(
            "run.check_voice_models",
            return_value=["Piper/Sherpa", "Kokoro-82M", "Qwen3-TTS"],
        ),
    ):
        run.check_prerequisites()
        captured = capsys.readouterr().out
        assert "espeak-ng not found" in captured
        assert "SLM engine not detected" in captured
        assert "Qwen3-TTS daemon not found" in captured
        assert "pnpm not found" in captured
        assert "Missing neural voice models" in captured


def test_build_pwa_no_package_json():
    """Verifies build_pwa aborts early if pwa/app/package.json is missing."""
    with patch("pathlib.Path.is_file", return_value=False):
        assert run.build_pwa() is False


def test_build_pwa_no_pnpm_with_prebuilt_bundle(capsys, monkeypatch):
    """Verifies fallback to prebuilt PWA bundle when pnpm is absent."""
    monkeypatch.delenv("PWA_STATIC_DIR", raising=False)

    def fake_is_file(self):
        return self.name in ("package.json", "index.html")

    with (
        patch("pathlib.Path.is_file", side_effect=fake_is_file, autospec=True),
        patch("run.resolve_pnpm", return_value=None),
    ):
        success = run.build_pwa()
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
        patch("run.resolve_pnpm", return_value=None),
    ):
        success = run.build_pwa()
        assert success is False
        captured = capsys.readouterr().out
        assert "pnpm not found and no pre-built bundle exists" in captured


def test_build_pwa_installs_dependencies_and_builds(monkeypatch):
    """Verifies pnpm install is executed if node_modules is missing, followed by build."""
    monkeypatch.delenv("PWA_STATIC_DIR", raising=False)

    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=False),
        patch("run.resolve_pnpm", return_value="/bin/pnpm"),
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_sub,
    ):
        assert run.build_pwa() is True
        assert mock_sub.call_count == 2
        assert mock_sub.call_args_list[0][0][0] == ["/bin/pnpm", "install"]
        assert mock_sub.call_args_list[1][0][0] == ["/bin/pnpm", "run", "build"]


def test_build_pwa_compilation_failure():
    """Verifies build_pwa handles compilation failure return codes cleanly."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=True),
        patch("run.resolve_pnpm", return_value="/bin/pnpm"),
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
    ):
        assert run.build_pwa() is False


def test_main_check_only(monkeypatch):
    """Verifies that --check-only halts before running build or uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--check-only"])
    with (
        patch("run.check_prerequisites") as mock_check,
        patch("run.build_pwa") as mock_build,
        patch("subprocess.run") as mock_sub,
    ):
        run.main()
        mock_check.assert_called_once()
        mock_build.assert_not_called()
        mock_sub.assert_not_called()


def test_main_no_build(monkeypatch):
    """Verifies that --no-build skips PWA build step and launches uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])

    def fake_is_file(self):
        return self.name == "logging_config.json"

    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa") as mock_build,
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", fake_is_file),
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_build.assert_not_called()
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "--log-config" in cmd


def test_main_omits_log_config_when_missing(monkeypatch):
    """Verifies --log-config is omitted when logging_config.json is absent."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch("run.build_pwa"),
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", return_value=False),
    ):
        run.main()
        mock_sync.assert_called_once()
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "--log-config" not in cmd


def test_resolve_llama_daemon_found_in_cache():
    """Verifies resolve_llama_daemon finds cached binary under .cache/bin/llama.cpp/."""

    def fake_is_file(self):
        return "llama-tts-daemon" in self.name or "llama-tts" in self.name

    with patch("pathlib.Path.is_file", fake_is_file):
        daemon_path = run.resolve_llama_daemon()
        assert daemon_path is not None
        assert "llama.cpp" in str(daemon_path)


def test_resolve_llama_daemon_found_in_path():
    """Verifies resolve_llama_daemon finds daemon via shutil.which if not in cache."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value="/usr/local/bin/llama-tts-daemon"),
    ):
        daemon_path = run.resolve_llama_daemon()
        assert daemon_path == Path("/usr/local/bin/llama-tts-daemon").resolve()


def test_resolve_llama_daemon_missing():
    """Verifies resolve_llama_daemon returns None when daemon is absent everywhere."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("shutil.which", return_value=None),
    ):
        assert run.resolve_llama_daemon() is None


def test_build_llama_success_and_force():
    """Verifies build_llama runs build_llama_tts.py with expected flags."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_run,
    ):
        assert run.build_llama(force=True) is True
        assert mock_run.call_count == 1
        assert "--force" in mock_run.call_args[0][0]


def test_build_llama_missing_script():
    """Verifies build_llama returns False when build script is missing."""
    with patch("pathlib.Path.is_file", return_value=False):
        assert run.build_llama() is False


def test_main_build_llama_flag(monkeypatch):
    """Verifies --build-llama triggers build_llama before check_only/uvicorn."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--build-llama", "--check-only"])
    with (
        patch("run.check_prerequisites"),
        patch("run.build_llama", return_value=True) as mock_build_llama,
        patch("subprocess.run") as mock_sub,
    ):
        run.main()
        mock_build_llama.assert_called_once_with(force=False)
        mock_sub.assert_not_called()


def test_main_build_llama_failure_exits(monkeypatch):
    """Verifies build failure causes main to exit with code 1."""
    import pytest

    monkeypatch.setattr(sys, "argv", ["run.py", "--build-llama"])
    with (
        patch("run.check_prerequisites"),
        patch("run.build_llama", return_value=False),
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    assert exc_info.value.code == 1


def test_sync_backend_success():
    """Verifies sync_backend executes uv sync --all-extras on backend directory."""
    with patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0),
    ) as mock_sub:
        assert run.sync_backend("/mock/bin/uv") is True
        assert mock_sub.call_count == 1
        cmd = mock_sub.call_args[0][0]
        assert cmd[:3] == ["/mock/bin/uv", "sync", "--all-extras"]
        assert "--directory" in cmd
        assert "backend" in str(cmd[cmd.index("--directory") + 1])


def test_sync_backend_failure():
    """Verifies sync_backend returns False when uv sync exits with non-zero code."""
    with patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1),
    ):
        assert run.sync_backend("/mock/bin/uv") is False


def test_main_no_sync_flag(monkeypatch):
    """Verifies --no-sync skips sync_backend execution."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--no-sync", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend") as mock_sync,
        patch("run.build_pwa"),
        patch("subprocess.run") as mock_sub,
        patch("pathlib.Path.is_file", return_value=False),
    ):
        run.main()
        mock_sync.assert_not_called()
        mock_sub.assert_called_once()


def test_main_sync_failure_exits(monkeypatch):
    """Verifies sync failure causes main to exit with code 1."""
    import pytest

    monkeypatch.setattr(sys, "argv", ["run.py", "--no-build"])
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=False),
        pytest.raises(SystemExit) as exc_info,
    ):
        run.main()
    assert exc_info.value.code == 1
