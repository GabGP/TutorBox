"""Tests for the TTS_QWEN_BATCH bounds and fallback (parse_int in qwen_settings.py)."""

import pytest

from core.config.constants import DEFAULT_TTS_QWEN_BATCH
from core.config.tts_settings import build_tts_config


@pytest.mark.parametrize("raw_value", ["15", "2049", "0", "-1", "big", "64.5", ""])
def test_out_of_range_or_invalid_batch_falls_back_to_default(monkeypatch, raw_value):
    """Values below 16, above 2048, or not integers fall back to the default batch."""
    monkeypatch.setenv("TTS_QWEN_BATCH", raw_value)
    assert build_tts_config().qwen_batch == DEFAULT_TTS_QWEN_BATCH


@pytest.mark.parametrize(
    ("raw_value", "expected_batch"),
    [("16", 16), ("2048", 2048), (" 64 ", 64)],
)
def test_batch_bounds_are_inclusive_and_surrounding_spaces_are_ignored(
    monkeypatch, raw_value, expected_batch
):
    """Both bounds are accepted, and int() ignores spaces around the number."""
    monkeypatch.setenv("TTS_QWEN_BATCH", raw_value)
    assert build_tts_config().qwen_batch == expected_batch
