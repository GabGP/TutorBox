"""Verifies engine-name normalization, the sweep catalogue and comma-list parsing."""

import pytest

from tools.benchmark.tts.sweep.engine_names import (
    DEFAULT_SWEEP_ENGINES,
    ENGINE_ALIASES,
    SUPPORTED_ENGINES,
    normalize_engine_name,
    parse_engine_names,
)

UNSUPPORTED_SUFFIX = "; use qwen3-tts for Qwen"


def test_catalogue_constants_match_the_sweep_definition():
    """Verifies the supported engine set, the Qwen alias and the default sweep list."""
    assert SUPPORTED_ENGINES == frozenset(
        {"qwen3-tts", "sherpa", "piper", "espeak", "kokoro", "melo", "moss-nano"}
    )
    assert ENGINE_ALIASES == {"qwen": "qwen3-tts"}
    assert DEFAULT_SWEEP_ENGINES == "qwen3-tts,sherpa,piper,espeak"


def test_default_engines_parse_to_four_names_in_order():
    """Verifies the default sweep string parses to the four engines in their order."""
    assert parse_engine_names(DEFAULT_SWEEP_ENGINES) == [
        "qwen3-tts",
        "sherpa",
        "piper",
        "espeak",
    ]


def test_qwen_alias_becomes_the_canonical_name():
    """Verifies the short Qwen alias is rewritten to qwen3-tts."""
    assert normalize_engine_name("qwen") == "qwen3-tts"
    assert parse_engine_names("qwen") == ["qwen3-tts"]


def test_upper_case_and_surrounding_spaces_are_normalized():
    """Verifies case and surrounding whitespace are removed before lookup."""
    assert normalize_engine_name("  QWEN ") == "qwen3-tts"
    assert normalize_engine_name(" Moss-Nano ") == "moss-nano"
    assert parse_engine_names("  PIPER , Sherpa ") == ["piper", "sherpa"]


def test_empty_items_between_commas_are_skipped():
    """Verifies empty and whitespace-only items between commas are ignored."""
    assert parse_engine_names("piper,,espeak,") == ["piper", "espeak"]
    assert parse_engine_names(" , piper, ,espeak") == ["piper", "espeak"]


def test_duplicates_collapse_keeping_first_position():
    """Verifies repeated engines, in any case, keep only their first position."""
    assert parse_engine_names("espeak,piper,ESPEAK,piper") == ["espeak", "piper"]


def test_qwen_and_its_canonical_name_collapse_to_one_entry():
    """Verifies qwen,qwen3-tts is parsed as a single qwen3-tts entry."""
    assert parse_engine_names("qwen,qwen3-tts") == ["qwen3-tts"]


def test_new_engines_are_accepted():
    """Verifies kokoro, melo and moss-nano pass validation in the given order."""
    assert parse_engine_names("kokoro,melo,moss-nano") == [
        "kokoro",
        "melo",
        "moss-nano",
    ]


def test_unsupported_engine_is_rejected_with_its_name():
    """Verifies a single unknown engine raises ValueError naming only that engine."""
    with pytest.raises(ValueError) as error_info:
        parse_engine_names("bogus")
    assert str(error_info.value) == f"unsupported engine(s): bogus{UNSUPPORTED_SUFFIX}"


def test_several_unsupported_engines_are_listed_once_each_in_first_seen_order():
    """Verifies unknown names are listed once each, in first-seen order."""
    with pytest.raises(ValueError) as error_info:
        parse_engine_names("bogus,piper,nope,bogus,Nope")
    assert (
        str(error_info.value)
        == f"unsupported engine(s): bogus, nope{UNSUPPORTED_SUFFIX}"
    )


@pytest.mark.parametrize("raw_engine_list", ["", " , ,"])
def test_list_without_any_engine_is_rejected(raw_engine_list):
    """Verifies an empty or blank engine list raises the at-least-one-engine error."""
    with pytest.raises(ValueError) as error_info:
        parse_engine_names(raw_engine_list)
    assert str(error_info.value) == "--engines must contain at least one engine"
