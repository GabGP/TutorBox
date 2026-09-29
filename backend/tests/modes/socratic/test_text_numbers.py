"""Accent-free matching, Spanish number words and number reading (modes/socratic)."""

from fractions import Fraction

import pytest

from modes.socratic.numbers import extract_numbers, format_value, to_fraction
from modes.socratic.text import Folded, fold, spanish_words


def test_fold_strips_accents_tilde_and_case():
    assert fold("¿Cuánto es la FRACCIÓN? Año, Cholq’ij") == (
        "¿cuanto es la fraccion? ano, cholq'ij"
    )


def test_folded_matches_words_stems_and_phrases():
    message = Folded.of("¿Cómo FUNCIONA la suma? Valor posicional")

    assert message.has("suma")
    assert message.has("sum*")
    assert not message.has("funcion")  # a verb, not "función"
    assert message.has("valor posicional")
    assert not message.has("valor relativo")
    assert message.has_any(["resta", "suma"])
    assert not message.has_any(["resta", "division*"])


def test_number_words_leave_out_articles():
    words = Folded.of("uno de sesenta y ocho, mil").number_words()

    assert words == {"sesenta", "ocho", "mil"}


@pytest.mark.parametrize(
    ("value", "words"),
    [
        (0, "cero"),
        (8, "ocho"),
        (21, "veintiuno"),
        (30, "treinta"),
        (68, "sesenta y ocho"),
        (100, "cien"),
        (101, "ciento uno"),
        (250, "doscientos cincuenta"),
        (1000, "mil"),
        (1500, "mil quinientos"),
        (3000, "tres mil"),
        (2021, "dos mil veintiuno"),
        (-1, ""),
        (1_000_000, ""),
    ],
)
def test_spanish_words(value, words):
    assert spanish_words(value) == words


@pytest.mark.parametrize(
    ("text", "values"),
    [
        ("23 + 45", [23, 45]),
        ("es 68.", [68]),
        ("1,000 y 10,000", [1000, 10000]),
        ("0,5 + 0.25", [Fraction(1, 2), Fraction(1, 4)]),
        ("1/2 + 3 / 4", [Fraction(1, 2), Fraction(3, 4)]),
        ("2x y x2", []),
        ("3/0", []),
    ],
)
def test_extract_numbers(text, values):
    assert extract_numbers(text) == values


def test_to_fraction():
    assert to_fraction("3", "0") is None
    assert to_fraction("12,500") == 12500
    assert to_fraction("2,5", "2") == Fraction(5, 4)


def test_format_value():
    assert format_value(Fraction(68)) == "68"
    assert format_value(Fraction(2500)) == "2,500"
    assert format_value(Fraction(12500)) == "12,500"
    assert format_value(Fraction(3, 4)) == "3/4"
    assert format_value(Fraction(3, 4), decimal=True) == "0.75"
