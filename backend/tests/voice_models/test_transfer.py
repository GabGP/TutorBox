"""Unit tests for the streaming download helper (tools/voice_models/transfer.py)."""

import io
import urllib.error
from unittest.mock import MagicMock, patch

from tools.voice_models import transfer


def _mock_http_response(payload: bytes, headers: dict[str, str]) -> MagicMock:
    """Builds a fake urlopen response that streams the given payload."""
    mock_response = MagicMock()
    mock_response.read.side_effect = io.BytesIO(payload).read
    mock_response.headers = headers
    return mock_response


def test_download_file_already_present(tmp_path):
    """Verifies download_file skips network call if file already exists with size > 0."""
    target = tmp_path / "model.onnx"
    target.write_bytes(b"existing-weights")

    with patch("urllib.request.urlopen") as mock_url:
        result = transfer.download_file("http://mock/model.onnx", target, force=False)
        assert result is True
        mock_url.assert_not_called()


def test_download_file_success(tmp_path):
    """Verifies download_file streams chunks, creates .part, and renames atomically."""
    target = tmp_path / "model.onnx"
    mock_response = _mock_http_response(b"fake-binary-data", {"Content-Length": "16"})

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        result = transfer.download_file("http://mock/model.onnx", target, force=True)
        assert result is True
        assert target.is_file()
        assert target.read_bytes() == b"fake-binary-data"
        assert not (tmp_path / "model.onnx.part").exists()


def test_download_file_failure_cleans_part(tmp_path):
    """Verifies download_file handles URLError and cleans up partial download file."""
    target = tmp_path / "model.onnx"
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Network unreachable"),
    ):
        result = transfer.download_file("http://mock/model.onnx", target)
        assert result is False
        assert not target.exists()
        assert not (tmp_path / "model.onnx.part").exists()


def test_download_file_removes_part_file_when_stream_breaks(tmp_path):
    """Verifies a connection dropped mid-stream leaves neither the file nor its .part."""
    target = tmp_path / "model.onnx"
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"first-chunk", OSError("Connection reset")]
    mock_response.headers = {"Content-Length": "64"}

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        result = transfer.download_file("http://mock/model.onnx", target)

    assert result is False
    assert not target.exists()
    assert not (tmp_path / "model.onnx.part").exists()


def test_download_file_prints_progress_when_length_is_known(tmp_path, capsys):
    """Verifies the percentage line is written when the server sends Content-Length."""
    target = tmp_path / "model.onnx"
    mock_response = _mock_http_response(b"fake-binary-data", {"Content-Length": "16"})

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        transfer.download_file("http://mock/model.onnx", target, label="Mock model")

    console_output = capsys.readouterr().out
    assert "Downloading Mock model..." in console_output
    assert "Mock model: 100.0%" in console_output
    assert "Successfully downloaded: model.onnx" in console_output


def test_download_file_skips_progress_without_content_length(tmp_path, capsys):
    """Verifies no percentage line is written when the server omits Content-Length."""
    target = tmp_path / "model.onnx"
    mock_response = _mock_http_response(b"fake-binary-data", {})

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        result = transfer.download_file("http://mock/model.onnx", target)

    assert result is True
    assert target.read_bytes() == b"fake-binary-data"
    assert "%" not in capsys.readouterr().out


def test_download_file_sends_downloader_user_agent(tmp_path):
    """Verifies the request identifies itself with the appliance User-Agent."""
    target = tmp_path / "model.onnx"
    mock_response = _mock_http_response(b"data", {})

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        transfer.download_file("http://mock/model.onnx", target)

    sent_request = mock_urlopen.call_args[0][0]
    assert sent_request.full_url == "http://mock/model.onnx"
    assert sent_request.get_header("User-agent") == (
        "Utz'tutor-Appliance-Downloader/1.0"
    )
    assert mock_urlopen.call_args.kwargs["timeout"] == 60.0
