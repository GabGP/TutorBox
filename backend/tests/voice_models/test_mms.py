"""Unit tests for the MMS Kʼicheʼ / Qʼeqchiʼ download step (tools/voice_models/mms.py)."""

from unittest.mock import patch

from tools.voice_models import catalog, mms

MODEL_NAMES = ("mms-tts-quc-dialect_central", "mms-tts-kek")


def _populate(models_dir, file_content=b"mms"):
    for model_name in MODEL_NAMES:
        model_dir = models_dir / "mms" / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        for file_name in catalog.MMS_FILE_NAMES:
            (model_dir / file_name).write_bytes(file_content)


def test_download_mms_fetches_every_file_of_both_checkpoints(tmp_path):
    """Verifies each checkpoint file comes from its Hugging Face repo into mms/<name>/."""
    with patch(
        "tools.voice_models.mms.download_file", return_value=True
    ) as mock_download:
        assert mms.download_mms(tmp_path, force=True) is True

    requested = [call.args[:2] for call in mock_download.call_args_list]
    assert requested == [
        (
            f"https://huggingface.co/facebook/{model_name}/resolve/main/{file_name}",
            tmp_path / "mms" / model_name / file_name,
        )
        for model_name in MODEL_NAMES
        for file_name in catalog.MMS_FILE_NAMES
    ]
    assert all(call.kwargs["force"] is True for call in mock_download.call_args_list)
    weight_labels = [
        call.kwargs["label"]
        for call in mock_download.call_args_list
        if call.args[1].name == "model.safetensors"
    ]
    assert len(weight_labels) == 2
    assert all(label.endswith("(~145 MB)") for label in weight_labels)


def test_download_mms_keeps_going_after_one_file_fails(tmp_path):
    """Verifies a failed file fails the step but the remaining files are still tried."""
    file_count = len(MODEL_NAMES) * len(catalog.MMS_FILE_NAMES)
    results = [False] + [True] * (file_count - 1)
    with patch(
        "tools.voice_models.mms.download_file", side_effect=results
    ) as mock_download:
        assert mms.download_mms(tmp_path) is False
    assert mock_download.call_count == file_count


def test_mms_models_present_needs_every_file(tmp_path):
    """Verifies presence means both checkpoints complete, with no empty file."""
    assert mms.mms_models_present(tmp_path) is False

    _populate(tmp_path)
    assert mms.mms_models_present(tmp_path) is True

    (tmp_path / "mms" / "mms-tts-kek" / "vocab.json").unlink()
    assert mms.mms_models_present(tmp_path) is False


def test_mms_models_present_treats_empty_files_as_missing(tmp_path):
    """Verifies a zero-byte file left by an interrupted download does not count."""
    _populate(tmp_path, file_content=b"")
    assert mms.mms_models_present(tmp_path) is False


def test_mms_model_dir_is_under_the_mms_folder(tmp_path):
    """Verifies each checkpoint has its own folder under mms/."""
    assert (
        mms.mms_model_dir(tmp_path, "mms-tts-kek") == tmp_path / "mms" / "mms-tts-kek"
    )
