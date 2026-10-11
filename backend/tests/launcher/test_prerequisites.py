"""Unit tests for the Utz'tutor launcher runtime prerequisite checks (tools/launcher/prerequisites.py)."""

from itertools import pairwise
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.launcher import paths, prerequisites


def _write_all_voice_models(models_dir: Path) -> None:
    """Creates every neural voice model file under the given models directory."""
    (models_dir / "es_ES-sharvard-medium.onnx").write_bytes(b"piper")
    kokoro_dir = models_dir / "kokoro-int8-multi-lang-v1_0"
    kokoro_dir.mkdir(parents=True)
    (kokoro_dir / "voices.bin").write_bytes(b"voices")
    qwen_dir = models_dir / "qwen"
    qwen_dir.mkdir(parents=True)
    (qwen_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf").write_bytes(b"gguf")
    (qwen_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf").write_bytes(b"mmproj")


def test_check_voice_models_reports_missing_models(tmp_path):
    """Verifies check_voice_models returns names of missing models."""
    missing = prerequisites.check_voice_models(tmp_path)
    assert "Piper/Sherpa" in missing
    assert "Kokoro-82M" in missing
    assert "Qwen3-TTS" in missing

    (tmp_path / "es_ES-sharvard-medium.onnx").write_bytes(b"weights")
    remaining = prerequisites.check_voice_models(tmp_path)
    assert "Piper/Sherpa" not in remaining
    assert "Kokoro-82M" in remaining


def test_check_voice_models_returns_empty_list_when_all_present(tmp_path):
    """Verifies check_voice_models reports nothing missing when every model file exists."""
    _write_all_voice_models(tmp_path)
    assert prerequisites.check_voice_models(tmp_path) == []


def test_check_voice_models_reports_qwen_missing_without_projector(tmp_path):
    """Verifies Qwen3-TTS is still reported missing when its mmproj companion file is absent."""
    _write_all_voice_models(tmp_path)
    (tmp_path / "qwen" / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf").unlink()
    assert prerequisites.check_voice_models(tmp_path) == ["Qwen3-TTS"]


def test_check_voice_models_defaults_to_tts_models_dir():
    """Verifies check_voice_models without an argument inspects paths.TTS_MODELS_DIR."""
    with patch(
        "pathlib.Path.is_file", autospec=True, return_value=False
    ) as is_file_mock:
        missing = prerequisites.check_voice_models()

    assert missing == ["Piper/Sherpa", "Kokoro-82M", "Qwen3-TTS"]
    checked_paths = [call.args[0] for call in is_file_mock.call_args_list]
    assert checked_paths
    assert all(path.is_relative_to(paths.TTS_MODELS_DIR) for path in checked_paths)


def test_check_prerequisites_all_reachable(capsys, monkeypatch):
    """Verifies prerequisite output when TTS, SLM, Qwen, and pnpm are all available."""
    monkeypatch.delenv("TTS_ESPEAK_BINARY", raising=False)
    monkeypatch.delenv("SLM_BASE_URL", raising=False)
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = None

    with (
        patch("shutil.which", return_value="/usr/bin/espeak-ng"),
        patch("urllib.request.urlopen", return_value=mock_cm),
        patch(
            "tools.launcher.prerequisites.resolve_llama_daemon",
            return_value=Path("/mock/llama-tts-daemon"),
        ),
        patch(
            "tools.launcher.prerequisites.resolve_pnpm", return_value="/usr/bin/pnpm"
        ),
        patch("tools.launcher.prerequisites.check_voice_models", return_value=[]),
    ):
        prerequisites.check_prerequisites()
        captured = capsys.readouterr().out
        assert "Found TTS engine" in captured
        assert "Local SLM engine reachable" in captured
        assert "Found Qwen3-TTS daemon" in captured
        assert "Found frontend package manager" in captured
        assert "Found all neural voice models" in captured


def test_check_prerequisites_all_missing(capsys, monkeypatch):
    """Verifies prerequisite warnings when engines are unreachable or missing."""
    monkeypatch.delenv("TTS_ESPEAK_BINARY", raising=False)
    monkeypatch.delenv("SLM_BASE_URL", raising=False)

    with (
        patch("shutil.which", return_value=None),
        patch("urllib.request.urlopen", side_effect=OSError("Unreachable")),
        patch("tools.launcher.prerequisites.resolve_llama_daemon", return_value=None),
        patch("tools.launcher.prerequisites.resolve_pnpm", return_value=None),
        patch(
            "tools.launcher.prerequisites.check_voice_models",
            return_value=["Piper/Sherpa", "Kokoro-82M", "Qwen3-TTS"],
        ),
    ):
        prerequisites.check_prerequisites()
        captured = capsys.readouterr().out
        assert "espeak-ng not found" in captured
        assert "SLM engine not detected" in captured
        assert "Qwen3-TTS daemon not found" in captured
        assert "pnpm not found" in captured
        assert "Missing neural voice models" in captured


def test_check_prerequisites_sections_print_in_order(capsys, monkeypatch):
    """Verifies the five prerequisite sections print in their documented order."""
    monkeypatch.delenv("TTS_ESPEAK_BINARY", raising=False)
    monkeypatch.delenv("SLM_BASE_URL", raising=False)
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = None

    with (
        patch("shutil.which", return_value="/usr/bin/espeak-ng"),
        patch("urllib.request.urlopen", return_value=mock_cm),
        patch(
            "tools.launcher.prerequisites.resolve_llama_daemon",
            return_value=Path("/mock/llama-tts-daemon"),
        ),
        patch(
            "tools.launcher.prerequisites.resolve_pnpm", return_value="/usr/bin/pnpm"
        ),
        patch("tools.launcher.prerequisites.check_voice_models", return_value=[]),
    ):
        prerequisites.check_prerequisites()

    captured = capsys.readouterr().out
    section_positions = [
        captured.index(section_marker)
        for section_marker in [
            "Found TTS engine",
            "Local SLM engine reachable",
            "Found Qwen3-TTS daemon",
            "Found frontend package manager",
            "Found all neural voice models",
        ]
    ]
    assert all(earlier < later for earlier, later in pairwise(section_positions))


def test_check_espeak_honours_custom_binary_env_var(capsys, monkeypatch):
    """Verifies TTS_ESPEAK_BINARY replaces the default espeak-ng lookup."""
    monkeypatch.setenv("TTS_ESPEAK_BINARY", "custom-espeak")

    with patch("shutil.which", return_value="/opt/custom-espeak") as which_mock:
        prerequisites._check_espeak()

    which_mock.assert_called_once_with("custom-espeak")
    assert "Found TTS engine: /opt/custom-espeak" in capsys.readouterr().out


def test_check_slm_honours_base_url_env_var(capsys, monkeypatch):
    """Verifies SLM_BASE_URL sets the endpoint probed and reported when the SLM is unreachable."""
    monkeypatch.setenv("SLM_BASE_URL", "http://127.0.0.1:9999/v1")

    with patch(
        "urllib.request.urlopen", side_effect=OSError("Unreachable")
    ) as urlopen_mock:
        prerequisites._check_slm()

    probed_request = urlopen_mock.call_args.args[0]
    assert probed_request.full_url == "http://127.0.0.1:9999/v1/models"
    assert (
        "SLM engine not detected at http://127.0.0.1:9999/v1" in capsys.readouterr().out
    )
