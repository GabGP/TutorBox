"""Unit tests for model presence checks and tier dispatch (status.py, tiers.py)."""

from unittest.mock import patch

import pytest

from tools.voice_models import catalog, status, tiers


def test_check_models_status_reports_correctly(tmp_path):
    """Verifies check_models correctly identifies existing vs missing model files."""
    status_empty = status.check_models(tmp_path)
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

    status_full = status.check_models(tmp_path)
    assert status_full == {"piper": True, "kokoro": True, "qwen": True}


def test_check_models_treats_empty_files_as_missing(tmp_path):
    """Verifies a zero-byte model left by an interrupted run does not count as present."""
    (tmp_path / "es_ES-sharvard-medium.onnx").write_bytes(b"")
    qwen_dir = tmp_path / "qwen"
    qwen_dir.mkdir()
    (qwen_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf").write_bytes(b"gguf")

    assert status.check_models(tmp_path) == {
        "piper": False,
        "kokoro": False,
        "qwen": False,
    }


def test_execute_download_routes_targets(tmp_path):
    """Verifies execute_download calls target handlers based on selected tier."""
    with (
        patch("tools.voice_models.tiers.download_piper", return_value=True) as m_piper,
        patch(
            "tools.voice_models.tiers.download_kokoro", return_value=True
        ) as m_kokoro,
        patch("tools.voice_models.tiers.download_qwen", return_value=True) as m_qwen,
    ):
        tiers.execute_download("minimal", tmp_path)
        m_piper.assert_called_once()
        m_kokoro.assert_not_called()
        m_qwen.assert_not_called()

    with (
        patch("tools.voice_models.tiers.download_piper", return_value=True) as m_piper,
        patch(
            "tools.voice_models.tiers.download_kokoro", return_value=True
        ) as m_kokoro,
        patch("tools.voice_models.tiers.download_qwen", return_value=True) as m_qwen,
    ):
        tiers.execute_download("all", tmp_path)
        m_piper.assert_called_once()
        m_kokoro.assert_called_once()
        m_qwen.assert_called_once()


@pytest.mark.parametrize(
    ("target", "expected_engine"),
    [("piper", "piper"), ("kokoro", "kokoro"), ("qwen", "qwen")],
)
def test_execute_download_single_engine_target(tmp_path, target, expected_engine):
    """Verifies a single-engine tier downloads that engine and no other."""
    with (
        patch("tools.voice_models.tiers.download_piper", return_value=True) as m_piper,
        patch(
            "tools.voice_models.tiers.download_kokoro", return_value=True
        ) as m_kokoro,
        patch("tools.voice_models.tiers.download_qwen", return_value=True) as m_qwen,
    ):
        assert tiers.execute_download(target, tmp_path, force=True) is True

    engine_mocks = {"piper": m_piper, "kokoro": m_kokoro, "qwen": m_qwen}
    for engine_name, engine_mock in engine_mocks.items():
        if engine_name == expected_engine:
            engine_mock.assert_called_once_with(tmp_path, force=True)
        else:
            engine_mock.assert_not_called()


def test_execute_download_keeps_going_after_one_engine_fails(tmp_path):
    """Verifies a failed engine fails the tier without skipping the remaining engines."""
    with (
        patch("tools.voice_models.tiers.download_piper", return_value=False),
        patch(
            "tools.voice_models.tiers.download_kokoro", return_value=True
        ) as m_kokoro,
        patch("tools.voice_models.tiers.download_qwen", return_value=True) as m_qwen,
    ):
        assert tiers.execute_download("all", tmp_path) is False
    m_kokoro.assert_called_once()
    m_qwen.assert_called_once()


def test_execute_download_creates_missing_models_directory(tmp_path):
    """Verifies the destination directory is created before any engine runs."""
    models_dir = tmp_path / "nested" / "tts"
    with patch("tools.voice_models.tiers.download_piper", return_value=True):
        assert tiers.execute_download("minimal", models_dir) is True
    assert models_dir.is_dir()


def test_execute_download_defaults_to_the_cache_models_directory(tmp_path):
    """Verifies the tier falls back to the catalog's default directory."""
    default_models_dir = tmp_path / "default-tts"
    with (
        patch("tools.voice_models.tiers.DEFAULT_MODELS_DIR", default_models_dir),
        patch("tools.voice_models.tiers.download_piper", return_value=True) as m_piper,
    ):
        assert tiers.execute_download() is True
    m_piper.assert_called_once_with(default_models_dir, force=False)


def test_default_models_directory_is_under_the_repo_cache():
    """Verifies models are stored in .cache/models/tts at the repository root."""
    assert catalog.DEFAULT_MODELS_DIR == (
        catalog.ROOT_DIR / ".cache" / "models" / "tts"
    )
    assert (catalog.ROOT_DIR / "run.py").is_file()
