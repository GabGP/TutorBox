"""Unit tests for the Mayan MMS voice engine (core/tts/engines/mms)."""

import importlib.machinery
import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.config import clear_settings_cache
from core.tts.engines.mms import MmsBackend
from core.tts.engines.mms.engine import CLAUSE_PAUSE_SECONDS
from core.tts.engines.mms.models import find_mms_dir, load_mms_voice
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError

VOCABULARY = {"|": 0, " ": 1, "a": 2, "e": 3, "i": 4, "o": 5, "s": 6, "t": 7}
SAMPLE_RATE = 16000
CLAUSE_SAMPLES = 800


@pytest.fixture
def mms_voices(tmp_path, monkeypatch):
    """Both exported voices under tmp_path, with a fake ONNX Runtime."""
    for checkpoint in ("mms-tts-quc-dialect_central", "mms-tts-kek"):
        voice_dir = tmp_path / checkpoint
        voice_dir.mkdir()
        (voice_dir / "model.onnx").write_bytes(b"onnx")
        (voice_dir / "vocab.json").write_text(json.dumps(VOCABULARY), "utf-8")
        (voice_dir / "config.json").write_text(
            json.dumps({"sampling_rate": SAMPLE_RATE}), "utf-8"
        )
    monkeypatch.setenv("TTS_MMS_MODEL_DIR", str(tmp_path))
    clear_settings_cache()
    session = MagicMock()
    session.run.return_value = [np.full((1, CLAUSE_SAMPLES), 0.5, dtype=np.float32)]
    fake_onnxruntime = MagicMock()
    fake_onnxruntime.__spec__ = importlib.machinery.ModuleSpec("onnxruntime", None)
    fake_onnxruntime.InferenceSession.return_value = session
    with patch.dict("sys.modules", {"onnxruntime": fake_onnxruntime}):
        yield tmp_path, fake_onnxruntime, session
    clear_settings_cache()


def test_engine_name_and_initial_state():
    backend = MmsBackend()
    assert backend.engine_name == "mms"
    assert backend.is_loaded() is False


def test_is_available_needs_a_mayan_language_and_its_voice(mms_voices):
    backend = MmsBackend()
    assert backend.is_available("quc") is True
    assert backend.is_available("kek") is True
    assert backend.is_available("es") is False
    assert backend.is_available(None) is False


def test_is_available_without_the_voice_files():
    """The test conftest points TTS_MMS_MODEL_DIR at a folder that does not exist."""
    assert MmsBackend().is_available("quc") is False
    assert find_mms_dir("quc") is None
    assert find_mms_dir("es") is None


def test_is_available_when_speech_is_disabled(mms_voices, monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    assert MmsBackend().is_available("quc") is False


def test_preload_and_unload_keep_one_voice_per_language(mms_voices):
    model_root, fake_onnxruntime, _ = mms_voices
    backend = MmsBackend()
    assert backend.preload("kek") >= 0.0
    assert backend.is_loaded() is True
    loaded_model = fake_onnxruntime.InferenceSession.call_args.args[0]
    assert loaded_model == str((model_root / "mms-tts-kek" / "model.onnx").resolve())
    backend.unload()
    assert backend.is_loaded() is False


def test_preload_refuses_other_languages_and_disabled_speech(mms_voices, monkeypatch):
    backend = MmsBackend()
    with pytest.raises(TTSUnavailableError, match="MMS has no voice for 'es'"):
        backend.preload("es")
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="disabled"):
        backend.preload("quc")


def test_synthesize_speaks_each_clause_with_a_pause(mms_voices):
    _, _, session = mms_voices
    wav = MmsBackend().synthesize("Este, es. 2", voice="quc")

    assert wav.startswith(b"RIFF")
    assert session.run.call_count == 3  # "Este", "es", "dos" (spoken from 2)
    first_clause = session.run.call_args_list[0].args[1]["input_ids"]
    assert first_clause.dtype == np.int64
    assert first_clause.tolist() == [[0, 3, 0, 6, 0, 7, 0, 3, 0]]
    pause_samples = int(SAMPLE_RATE * CLAUSE_PAUSE_SECONDS)
    expected_samples = 3 * CLAUSE_SAMPLES + 2 * pause_samples
    assert (len(wav) - 44) // 2 == expected_samples


def test_synthesize_reuses_the_loaded_voice(mms_voices):
    _, fake_onnxruntime, _ = mms_voices
    backend = MmsBackend()
    backend.synthesize("sate", voice="kek")
    backend.synthesize("tose", voice="kek")
    assert fake_onnxruntime.InferenceSession.call_count == 1


def test_synthesize_without_speakable_text_fails(mms_voices):
    with pytest.raises(TTSSynthesisError, match="no text this voice can speak"):
        MmsBackend().synthesize("¿? ...", voice="quc")


def test_synthesize_reports_runtime_errors(mms_voices):
    _, _, session = mms_voices
    session.run.side_effect = RuntimeError("bad input")
    with pytest.raises(TTSSynthesisError, match="MMS synthesis failed: bad input"):
        MmsBackend().synthesize("sate", voice="quc")


def test_synthesize_refuses_disabled_speech(mms_voices, monkeypatch):
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="disabled"):
        MmsBackend().synthesize("sate", voice="quc")


def test_load_without_onnxruntime_is_unavailable(mms_voices):
    with (
        patch.dict("sys.modules", {"onnxruntime": None}),
        pytest.raises(TTSUnavailableError, match="onnxruntime is not installed"),
    ):
        load_mms_voice("quc")


def test_load_without_the_voice_names_the_setup_command():
    with (
        patch.dict("sys.modules", {"onnxruntime": MagicMock()}),
        pytest.raises(TTSUnavailableError, match="--download-models mayan"),
    ):
        load_mms_voice("kek")


def test_load_without_a_config_uses_the_mms_rate(mms_voices):
    model_root, _, _ = mms_voices
    (model_root / "mms-tts-kek" / "config.json").unlink()
    assert load_mms_voice("kek").sample_rate == SAMPLE_RATE
    assert load_mms_voice("kek").vocabulary == VOCABULARY
