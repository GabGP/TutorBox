"""Unit tests for TutorBox TTS model downloader (tools/download_models.py) and runner integration."""

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run
from tools import download_models


def test_download_file_already_present(tmp_path):
    """Verifies download_file skips network call if file already exists with size > 0."""
    target = tmp_path / "model.onnx"
    target.write_bytes(b"existing-weights")

    with patch("urllib.request.urlopen") as mock_url:
        result = download_models.download_file(
            "http://mock/model.onnx", target, force=False
        )
        assert result is True
        mock_url.assert_not_called()


def test_download_file_success(tmp_path):
    """Verifies download_file streams chunks, creates .part, and renames atomically."""
    target = tmp_path / "model.onnx"
    mock_response = MagicMock()
    mock_response.read.side_effect = io.BytesIO(b"fake-binary-data").read
    mock_response.headers = {"Content-Length": "16"}

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        result = download_models.download_file(
            "http://mock/model.onnx", target, force=True
        )
        assert result is True
        assert target.is_file()
        assert target.read_bytes() == b"fake-binary-data"
        assert not (tmp_path / "model.onnx.part").exists()


def test_download_file_failure_cleans_part(tmp_path):
    """Verifies download_file handles URLError and cleans up partial download file."""
    import urllib.error

    target = tmp_path / "model.onnx"
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Network unreachable"),
    ):
        result = download_models.download_file("http://mock/model.onnx", target)
        assert result is False
        assert not target.exists()
        assert not (tmp_path / "model.onnx.part").exists()


def test_generate_sherpa_tokens_creates_tokens(tmp_path):
    """Verifies generate_sherpa_tokens extracts phoneme_id_map to formatted lines."""
    json_path = tmp_path / "model.onnx.json"
    tokens_path = tmp_path / "tokens.txt"
    json_path.write_text(
        json.dumps({"phoneme_id_map": {"a": [1], "b": [2], "_": [0]}}),
        encoding="utf-8",
    )

    success = download_models.generate_sherpa_tokens(json_path, tokens_path)
    assert success is True
    assert tokens_path.is_file()
    lines = tokens_path.read_text(encoding="utf-8").splitlines()
    assert "a 1" in lines
    assert "b 2" in lines


def test_generate_sherpa_tokens_missing_json(tmp_path):
    """Verifies generate_sherpa_tokens returns False when json config does not exist."""
    json_path = tmp_path / "nonexistent.json"
    tokens_path = tmp_path / "tokens.txt"
    assert download_models.generate_sherpa_tokens(json_path, tokens_path) is False


def test_safe_extract_tar_detects_traversal(tmp_path):
    """Verifies safe extract rejects tar archives attempting path traversal."""
    import pytest

    mock_member = MagicMock()
    mock_member.name = "../outside.txt"

    mock_archive = MagicMock()
    mock_archive.getmembers.return_value = [mock_member]

    with patch("tarfile.open") as mock_tar_open:
        mock_tar_open.return_value.__enter__.return_value = mock_archive
        with pytest.raises(RuntimeError, match="Path traversal detected"):
            download_models._safe_extract_tar(tmp_path / "fake.tar", tmp_path)


def test_check_models_status_reports_correctly(tmp_path):
    """Verifies check_models correctly identifies existing vs missing model files."""
    status_empty = download_models.check_models(tmp_path)
    assert status_empty == {"piper": False, "kokoro": False, "qwen": False}

    # Populate piper
    (tmp_path / "es_ES-sharvard-medium.onnx").write_bytes(b"piper")
    # Populate kokoro
    kokoro_dir = tmp_path / "kokoro-int8-multi-lang-v1_0"
    kokoro_dir.mkdir(parents=True)
    (kokoro_dir / "voices.bin").write_bytes(b"voices")
    # Populate qwen
    qwen_dir = tmp_path / "qwen"
    qwen_dir.mkdir(parents=True)
    (qwen_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf").write_bytes(b"gguf")
    (qwen_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf").write_bytes(b"mmproj")

    status_full = download_models.check_models(tmp_path)
    assert status_full == {"piper": True, "kokoro": True, "qwen": True}


def test_execute_download_routes_targets(tmp_path):
    """Verifies execute_download calls target handlers based on selected tier."""
    with (
        patch("tools.download_models.download_piper", return_value=True) as m_piper,
        patch("tools.download_models.download_kokoro", return_value=True) as m_kokoro,
        patch("tools.download_models.download_qwen", return_value=True) as m_qwen,
    ):
        download_models.execute_download("minimal", tmp_path)
        m_piper.assert_called_once()
        m_kokoro.assert_not_called()
        m_qwen.assert_not_called()

    with (
        patch("tools.download_models.download_piper", return_value=True) as m_piper,
        patch("tools.download_models.download_kokoro", return_value=True) as m_kokoro,
        patch("tools.download_models.download_qwen", return_value=True) as m_qwen,
    ):
        download_models.execute_download("all", tmp_path)
        m_piper.assert_called_once()
        m_kokoro.assert_called_once()
        m_qwen.assert_called_once()


def test_run_check_voice_models_helper(tmp_path):
    """Verifies run.check_voice_models returns names of missing models."""
    missing = run.check_voice_models(tmp_path)
    assert "Piper/Sherpa" in missing
    assert "Kokoro-82M" in missing
    assert "Qwen3-TTS" in missing

    (tmp_path / "es_ES-sharvard-medium.onnx").write_bytes(b"weights")
    remaining = run.check_voice_models(tmp_path)
    assert "Piper/Sherpa" not in remaining
    assert "Kokoro-82M" in remaining


def test_run_main_download_models_flag(monkeypatch):
    """Verifies run.py --download-models executes tools/download_models.py before exit."""
    import subprocess

    monkeypatch.setattr(
        sys, "argv", ["run.py", "--download-models", "minimal", "--check-only"]
    )
    with (
        patch("run.check_prerequisites"),
        patch("run.sync_backend", return_value=True) as mock_sync,
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_sub,
    ):
        run.main()
        mock_sync.assert_called_once()
        assert mock_sub.call_count == 1
        cmd = mock_sub.call_args[0][0]
        assert "download_models.py" in str(cmd[1])
        assert "--target" in cmd
        assert "minimal" in cmd
