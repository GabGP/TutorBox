"""Unit tests for the MMS text helpers: Spanish number words and token ids."""

import pytest

from core.tts.engines.mms.numbers import spanish_number_words, spell_out_numbers
from core.tts.engines.mms.tokens import (
    BLANK_TOKEN_ID,
    clause_token_ids,
    split_clauses,
)

KICHE_VOCABULARY = {"|": 0, " ": 1, "a": 2, "c": 3, "h": 4, "o": 5, "l": 6, "ꞌ": 7}
QEQCHI_VOCABULARY = {"|": 0, " ": 1, "a": 2, "'": 3, "n": 4}


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "cero"),
        (7, "siete"),
        (16, "dieciséis"),
        (21, "veintiuno"),
        (30, "treinta"),
        (67, "sesenta y siete"),
        (100, "cien"),
        (101, "ciento uno"),
        (300, "trescientos"),
        (999, "novecientos noventa y nueve"),
        (1000, "mil"),
        (1001, "mil uno"),
        (2500, "dos mil quinientos"),
        (21000, "veintiún mil"),
        (31000, "treinta y un mil"),
        (1_000_000, "un millón"),
        (2_000_001, "dos millones uno"),
        (21_000_000, "veintiún millones"),
        (1_001_000, "un millón mil"),
    ],
)
def test_spanish_number_words(number, words):
    assert spanish_number_words(number) == words


def test_very_large_numbers_are_read_digit_by_digit():
    assert spanish_number_words(1_234_567_890) == (
        "uno dos tres cuatro cinco seis siete ocho nueve cero"
    )


def test_spell_out_numbers_replaces_whole_numbers_and_decimals():
    assert spell_out_numbers("El 67 por ciento; 3.75 y 2 coma 5.") == (
        "El sesenta y siete por ciento; tres punto setenta y cinco y dos coma cinco."
    )


def test_split_clauses_cuts_at_punctuation_and_spaced_dashes():
    assert split_clauses("¿Hola? Uno, dos; tres: cuatro — cinco.\n(seis)") == [
        "Hola",
        "Uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
    ]
    assert split_clauses(" ... ") == []


def test_clause_token_ids_lowercases_drops_and_interleaves_blanks():
    token_ids = clause_token_ids("HOLA  xyz", KICHE_VOCABULARY)
    assert token_ids == [0, 4, 0, 5, 0, 6, 0, 2, 0]
    assert token_ids[0] == BLANK_TOKEN_ID


def test_clause_token_ids_maps_glottal_stops_to_the_voice_mark():
    """Each checkpoint knows one glottal-stop mark; the others are mapped to it."""
    assert clause_token_ids("ca'", KICHE_VOCABULARY) == [0, 3, 0, 2, 0, 7, 0]
    assert clause_token_ids("aꞌn", QEQCHI_VOCABULARY) == [0, 2, 0, 3, 0, 4, 0]


def test_clause_token_ids_keeps_a_mark_when_the_voice_has_none():
    vocabulary = {"|": 0, "a": 1}
    assert clause_token_ids("a'a", vocabulary) == [0, 1, 0, 1, 0]


def test_clause_token_ids_is_empty_when_nothing_can_be_spoken():
    assert clause_token_ids("123 ¿?", KICHE_VOCABULARY) == []
