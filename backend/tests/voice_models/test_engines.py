"""Unit tests for the per-engine download steps (tools/voice_models/engines.py)."""

import tarfile
from unittest.mock import patch

from tools.voice_models import engines

PIPER_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium"
)
KOKORO_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    "kokoro-int8-multi-lang-v1_0.tar.bz2"
)
QWEN_URL = "https://huggingface.co/ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF/resolve/main"


def test_download_piper_fetches_model_and_config_then_converts(tmp_path):
    """Verifies Piper fetches the model and its config, then builds the Sherpa files."""
    with (
        patch(
            "tools.voice_models.engines.download_file", return_value=True
        ) as mock_download,
        patch("tools.voice_models.engines.generate_sherpa_tokens") as mock_tokens,
        patch("tools.voice_models.engines.generate_sherpa_model") as mock_model,
    ):
        assert engines.download_piper(tmp_path, force=True) is True

    requested = [call.args[:2] for call in mock_download.call_args_list]
    assert requested == [
        (
            f"{PIPER_URL}/es_ES-sharvard-medium.onnx",
            tmp_path / "es_ES-sharvard-medium.onnx",
        ),
        (
            f"{PIPER_URL}/es_ES-sharvard-medium.onnx.json",
            tmp_path / "es_ES-sharvard-medium.onnx.json",
        ),
    ]
    assert all(call.kwargs["force"] is True for call in mock_download.call_args_list)
    mock_tokens.assert_called_once_with(
        tmp_path / "es_ES-sharvard-medium.onnx.json",
        tmp_path / "tokens_es_ES-sharvard-medium.txt",
    )
    mock_model.assert_called_once_with(
        tmp_path / "es_ES-sharvard-medium.onnx",
        tmp_path / "es_ES-sharvard-medium.onnx.json",
        tmp_path / "es_ES-sharvard-medium.sherpa.onnx",
        force=True,
    )


def test_download_piper_skips_conversion_when_a_download_fails(tmp_path):
    """Verifies no Sherpa file is generated when the config download fails."""
    with (
        patch("tools.voice_models.engines.download_file", side_effect=[True, False]),
        patch("tools.voice_models.engines.generate_sherpa_tokens") as mock_tokens,
        patch("tools.voice_models.engines.generate_sherpa_model") as mock_model,
    ):
        assert engines.download_piper(tmp_path) is False
    mock_tokens.assert_not_called()
    mock_model.assert_not_called()


def test_download_kokoro_skips_bundle_already_on_disk(tmp_path, capsys):
    """Verifies an extracted Kokoro bundle is reused without touching the network."""
    kokoro_dir = tmp_path / "kokoro-int8-multi-lang-v1_0"
    kokoro_dir.mkdir()
    (kokoro_dir / "voices.bin").write_bytes(b"voices")
    (kokoro_dir / "model.int8.onnx").write_bytes(b"weights")

    with patch("tools.voice_models.engines.download_file") as mock_download:
        assert engines.download_kokoro(tmp_path) is True
    mock_download.assert_not_called()
    assert "Already present: Kokoro-82M bundle" in capsys.readouterr().out


def test_download_kokoro_force_downloads_bundle_already_on_disk(tmp_path):
    """Verifies force=True fetches the archive again over an existing bundle."""
    kokoro_dir = tmp_path / "kokoro-int8-multi-lang-v1_0"
    kokoro_dir.mkdir()
    (kokoro_dir / "voices.bin").write_bytes(b"voices")
    (kokoro_dir / "model.onnx").write_bytes(b"weights")

    with (
        patch(
            "tools.voice_models.engines.download_file", return_value=True
        ) as mock_download,
        patch("tools.voice_models.engines.safe_extract_tar"),
    ):
        assert engines.download_kokoro(tmp_path, force=True) is True
    mock_download.assert_called_once()
    assert mock_download.call_args.kwargs["force"] is True


def test_download_kokoro_stops_when_archive_download_fails(tmp_path):
    """Verifies extraction is never attempted when the archive download fails."""
    with (
        patch("tools.voice_models.engines.download_file", return_value=False),
        patch("tools.voice_models.engines.safe_extract_tar") as mock_extract,
    ):
        assert engines.download_kokoro(tmp_path) is False
    mock_extract.assert_not_called()


def test_download_kokoro_extracts_then_deletes_archive(tmp_path):
    """Verifies the archive is unpacked into the models directory and then removed."""
    tar_path = tmp_path / "kokoro-int8-multi-lang-v1_0.tar.bz2"

    def write_archive(url, destination, **keyword_arguments):
        destination.write_bytes(b"compressed-bundle")
        return True

    with (
        patch(
            "tools.voice_models.engines.download_file", side_effect=write_archive
        ) as mock_download,
        patch("tools.voice_models.engines.safe_extract_tar") as mock_extract,
    ):
        assert engines.download_kokoro(tmp_path) is True

    assert mock_download.call_args.args[:2] == (KOKORO_URL, tar_path)
    mock_extract.assert_called_once_with(tar_path, tmp_path)
    assert not tar_path.exists()


def test_download_kokoro_reports_extraction_failure(tmp_path, capsys):
    """Verifies a corrupt archive is reported as a failure instead of raising."""
    with (
        patch("tools.voice_models.engines.download_file", return_value=True),
        patch(
            "tools.voice_models.engines.safe_extract_tar",
            side_effect=tarfile.TarError("truncated archive"),
        ),
    ):
        assert engines.download_kokoro(tmp_path) is False
    assert "Extraction failed: truncated archive" in capsys.readouterr().out


def test_download_qwen_fetches_weights_and_projector(tmp_path):
    """Verifies Qwen3-TTS fetches the GGUF weights and the mmproj into qwen/."""
    with patch(
        "tools.voice_models.engines.download_file", return_value=True
    ) as mock_download:
        assert engines.download_qwen(tmp_path) is True

    requested = [call.args[:2] for call in mock_download.call_args_list]
    assert requested == [
        (
            f"{QWEN_URL}/Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf",
            tmp_path / "qwen" / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf",
        ),
        (
            f"{QWEN_URL}/mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf",
            tmp_path / "qwen" / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf",
        ),
    ]


def test_download_qwen_fails_when_projector_download_fails(tmp_path):
    """Verifies Qwen3-TTS reports failure when only the weights could be fetched."""
    with patch("tools.voice_models.engines.download_file", side_effect=[True, False]):
        assert engines.download_qwen(tmp_path) is False
