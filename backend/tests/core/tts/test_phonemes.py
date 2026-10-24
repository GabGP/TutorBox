"""Unit tests for the espeak-ng phonemes handed to sherpa-onnx 2.x."""

from unittest.mock import MagicMock, patch

import pytest

from core.tts.engines.phonemes import (
    phoneme_generation_config,
    phonemize_to_codepoints,
)
from core.tts.exceptions import TTSUnavailableError


def test_phonemize_spanish_text_into_codepoints():
    sentences = phonemize_to_codepoints("Hola.", "es")
    assert len(sentences) == 1
    spoken = "".join(chr(codepoint) for codepoint in sentences[0])
    assert spoken == "ˈola."


def test_phonemize_keeps_one_list_per_sentence():
    sentences = phonemize_to_codepoints("Hola. ¿Cuánto es tres más cuatro?", "es")
    assert len(sentences) == 2
    assert chr(sentences[1][-1]) == "?"


def test_phonemize_shares_the_piper_phonemizer():
    from piper import voice as piper_voice

    phonemize_to_codepoints("uno", "es")
    shared_phonemizer = piper_voice._ESPEAK_PHONEMIZER
    assert shared_phonemizer is not None

    phonemize_to_codepoints("dos", "es")
    assert piper_voice._ESPEAK_PHONEMIZER is shared_phonemizer


def test_phonemize_without_piper_is_unavailable():
    with (
        patch.dict("sys.modules", {"piper": None, "piper.phonemize_espeak": None}),
        pytest.raises(TTSUnavailableError, match="piper-tts"),
    ):
        phonemize_to_codepoints("Hola", "es")


def test_generation_config_carries_speaker_speed_and_phonemes():
    mock_sherpa = MagicMock()
    with patch.dict("sys.modules", {"sherpa_onnx": mock_sherpa}):
        config = phoneme_generation_config("Hola.", "es", speaker_id=53, speed=1.1)

    assert config is mock_sherpa.GenerationConfig.return_value
    assert config.sid == 53
    assert config.speed == 1.1
    assert config.phoneme_codepoints == phonemize_to_codepoints("Hola.", "es")
