"""Unit tests for guarded tar extraction (tools/voice_models/archive.py)."""

import tarfile
from unittest.mock import MagicMock, patch

import pytest

from tools.voice_models import archive


def test_safe_extract_tar_detects_traversal(tmp_path):
    """Verifies safe extract rejects tar archives attempting path traversal."""
    mock_member = MagicMock()
    mock_member.name = "../outside.txt"

    mock_archive = MagicMock()
    mock_archive.getmembers.return_value = [mock_member]

    with patch("tarfile.open") as mock_tar_open:
        mock_tar_open.return_value.__enter__.return_value = mock_archive
        with pytest.raises(RuntimeError, match="Path traversal detected"):
            archive.safe_extract_tar(tmp_path / "fake.tar", tmp_path)
    mock_archive.extractall.assert_not_called()


def test_safe_extract_tar_extracts_members_inside_destination(tmp_path):
    """Verifies a well-formed archive is unpacked under the destination directory."""
    source_file = tmp_path / "voices.bin"
    source_file.write_bytes(b"voice-embeddings")
    tar_path = tmp_path / "bundle.tar.bz2"
    with tarfile.open(tar_path, "w:bz2") as bundle:
        bundle.add(source_file, arcname="kokoro/voices.bin")
    destination_dir = tmp_path / "models"
    destination_dir.mkdir()

    archive.safe_extract_tar(tar_path, destination_dir)

    extracted_file = destination_dir / "kokoro" / "voices.bin"
    assert extracted_file.read_bytes() == b"voice-embeddings"
