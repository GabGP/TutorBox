"""Reads the numbers a child (or the model) writes: 68, 1,000, 0.5, 0,5 and 3/4.

Guatemalan schools write a point for decimals and group thousands with commas
(10,000), so a comma followed by exactly three digits is a thousands separator.
A comma followed by one or two digits is read as a decimal comma (0,5), which is
how many children type it. Values are exact Fractions, never floats.
"""

import re
from fractions import Fraction

__all__ = ["extract_numbers", "format_value", "to_fraction"]

_THOUSANDS = re.compile(r"\d{1,3}(?:,\d{3})+")
_NUMBER = re.compile(
    r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+(?![\d,])|\d+(?:[.,]\d+)?)"
    r"(?:\s*/\s*(\d+))?(?![\w/])"
)


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
