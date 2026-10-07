"""Reads the numbers a child (or the model) writes: 68, 1,000, 0.5, 0,5, 3/4 and
sesenta y ocho.

Guatemalan schools write a point for decimals and group thousands with commas
(10,000), so a comma followed by exactly three digits is a thousands separator.
A comma followed by one or two digits is read as a decimal comma (0,5), which is
how many children type it. Values are exact Fractions, never floats.
"""

import re
from fractions import Fraction

from modes.socratic.text import fold, spanish_words

__all__ = ["digits_for_words", "extract_numbers", "format_value", "to_fraction"]

_THOUSANDS = re.compile(r"\d{1,3}(?:,\d{3})+")
_NUMBER = re.compile(
    r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+(?![\d,])|\d+(?:[.,]\d+)?)"
    r"(?:\s*/\s*(\d+))?(?![\w/])"
)
# Number words as spanish_words writes them, 0 to 999,999. "ciento" needs tens or
# units after it ("por ciento" is a percentage) and a lone "uno" is an article.
_WORD_VALUES = {
    spanish_words(n): n
    for n in (*range(30), *range(30, 100, 10), *range(100, 1000, 100), 1000)
} | {"ciento": 100}
_ACCENTED = str.maketrans({v: f"[{v}{a}]" for v, a in zip("aeiou", "áéíóú")})
_WORD = "|".join(
    w.translate(_ACCENTED) for w in sorted(_WORD_VALUES, key=len, reverse=True)
)
_RUN = re.compile(rf"\b(?:{_WORD})(?:\s+(?:y\s+)?(?:{_WORD}))*\b", re.IGNORECASE)
_CLASSES = ((100, 999), (30, 99), (0, 29))  # hundreds, then tens, then units


def digits_for_words(text: str) -> str:
    """'sesenta y ocho' → '68', 'dos mil quinientos' → '2500'; other words stay."""
    return _RUN.sub(lambda match: _digits(match.group(0)), text)


def _digits(run: str) -> str:
    words, pieces, i = fold(run).split(), [], 0
    while i < len(words):
        value, end = _number(words, i)
        pieces.append(str(value) if end > i else words[i])
        i = max(end, i + 1)
    return " ".join(pieces) if pieces != words else run


def _number(words: list[str], i: int) -> tuple[int, int]:
    """The number that starts at words[i] and the index after it (i if none)."""
    head, end = _below_thousand(words, i)
    if end < len(words) and words[end] == "mil":
        rest, after = _below_thousand(words, end + 1)
        return (head if end > i else 1) * 1000 + rest, after
    if words[i:end] in (["uno"], ["ciento"]):
        return 0, i
    return head, end


def _below_thousand(words: list[str], i: int) -> tuple[int, int]:
    total, j = 0, i
    for low, high in _CLASSES:
        value = _WORD_VALUES.get(words[j], -1) if j < len(words) else -1
        if not low <= value <= high:
            continue
        total, j = total + value, j + 1
        if words[j - 1] == "cien" or low == 0:
            break
        if low == 30:  # "treinta y dos": only a unit 1-9 follows, after "y"
            after = words[j : j + 2]
            if after[:1] == ["y"] and 1 <= _WORD_VALUES.get(after[-1], 0) <= 9:
                total, j = total + _WORD_VALUES[after[-1]], j + 2
            break
    return total, j


def to_fraction(raw: str, denominator: str | None = None) -> Fraction | None:
    """Converts '1,000', '0.5', '0,5' (and an optional '/4') to an exact value."""
    if _THOUSANDS.fullmatch(raw):
        value = Fraction(int(raw.replace(",", "")))
    else:
        value = Fraction(raw.replace(",", "."))
    if denominator is None:
        return value
    divisor = int(denominator)
    return value / divisor if divisor else None


def extract_numbers(text: str) -> list[Fraction]:
    """Every number written with digits in the text, in order."""
    values: list[Fraction] = []
    for match in _NUMBER.finditer(text):
        value = to_fraction(match.group(1), match.group(2))
        if value is not None:
            values.append(value)
    return values


def format_value(value: Fraction, decimal: bool = False) -> str:
    """68, 2,500, 3/4, or 0.75 when the problem was written with decimals."""
    if value.denominator == 1:
        return f"{value.numerator:,}"
    if decimal:
        return format(float(value), "g")
    return f"{value.numerator}/{value.denominator}"
