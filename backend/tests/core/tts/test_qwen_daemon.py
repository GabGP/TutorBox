"""Unit tests for Qwen3-TTS persistent daemon client."""

import queue
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from core.tts.engines.qwen.daemon import QwenDaemonClient
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError


def _create_mock_popen(stdout_lines: list[str], returncode: int | None = None):
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.poll.return_value = returncode
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.read.return_value = "cuda error log"
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline.side_effect = list(stdout_lines) + [""]
    return mock_proc


def test_daemon_client_start_success():
    mock_proc = _create_mock_popen(["READY\n"])
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon", "--daemon"], startup_timeout=1.0)
        assert client.is_alive()
        client.close()


def test_daemon_client_start_os_error():
    with (
        patch("subprocess.Popen", side_effect=OSError("Exec failed")),
        pytest.raises(TTSUnavailableError, match="Failed to spawn Qwen daemon"),
    ):
        QwenDaemonClient(["invalid-bin"], startup_timeout=1.0)


def test_daemon_client_start_not_ready():
    mock_proc = _create_mock_popen(["ERROR_CUDA_INIT\n"])
    with (
        patch("subprocess.Popen", return_value=mock_proc),
        pytest.raises(TTSUnavailableError, match="Qwen daemon startup failed"),
    ):
        QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)


def test_daemon_client_start_timeout():
    mock_proc = _create_mock_popen([])
    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch.object(queue.Queue, "get", side_effect=queue.Empty),
        pytest.raises(TTSUnavailableError, match="timed out"),
    ):
        QwenDaemonClient(["llama-tts-daemon"], startup_timeout=0.01)


def test_daemon_client_synthesize_success(tmp_path):
    mock_proc = _create_mock_popen(
        ["READY\n", "DONE\ttotal=0.812\tprompt_eval=0.081\n"]
    )
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        res = client.synthesize("es", out_wav, "Hola\tMundo\n", timeout_seconds=1.0)
        assert res.startswith("DONE")
        mock_proc.stdin.write.assert_called_with(f"SYNTH\tes\t{out_wav}\tHola Mundo\n")
        client.close()


def test_daemon_client_synthesize_not_running(tmp_path):
    mock_proc = _create_mock_popen(["READY\n"], returncode=1)
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        with pytest.raises(TTSSynthesisError, match="not running"):
            client.synthesize("es", out_wav, "Hola", timeout_seconds=1.0)


def test_daemon_client_synthesize_timeout(tmp_path):
    mock_proc = _create_mock_popen(["READY\n"])
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        with (
            patch.object(client._stdout_queue, "get", side_effect=queue.Empty),
            pytest.raises(TTSSynthesisError, match="synthesis timed out"),
        ):
            client.synthesize("es", out_wav, "Hola", timeout_seconds=0.01)


def test_daemon_client_synthesize_io_error(tmp_path):
    mock_proc = _create_mock_popen(["READY\n"])
    mock_proc.stdin.write.side_effect = OSError("Broken pipe")
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        with pytest.raises(TTSSynthesisError, match="Failed to communicate"):
            client.synthesize("es", out_wav, "Hola", timeout_seconds=1.0)


def test_daemon_client_synthesize_unexpected_eof(tmp_path):
    mock_proc = _create_mock_popen(["READY\n", ""])
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        with pytest.raises(TTSSynthesisError, match="terminated unexpectedly"):
            client.synthesize("es", out_wav, "Hola", timeout_seconds=1.0)


def test_daemon_client_synthesize_error_response(tmp_path):
    mock_proc = _create_mock_popen(["READY\n", "ERR\tsynthesis_failed\n"])
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        out_wav = tmp_path / "test.wav"
        with pytest.raises(TTSSynthesisError, match="synthesis failed: ERR"):
            client.synthesize("es", out_wav, "Hola", timeout_seconds=1.0)


def test_daemon_client_close_kill_on_wait_failure():
    mock_proc = _create_mock_popen(["READY\n"])
    mock_proc.wait.side_effect = subprocess.TimeoutExpired("llama-tts-daemon", 2.0)
    with patch("subprocess.Popen", return_value=mock_proc):
        client = QwenDaemonClient(["llama-tts-daemon"], startup_timeout=1.0)
        client.close()
        mock_proc.kill.assert_called_once()
        assert not client.is_alive()
