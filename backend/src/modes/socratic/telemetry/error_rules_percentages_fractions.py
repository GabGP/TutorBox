"""Misconceptions with percentages (20% de 50) and with adding or subtracting fractions.

Only the two shapes find_problem writes are read: '20% de 50', and exactly two
fractions joined by + or -. Any other text gives no predictions.
"""

import re
from fractions import Fraction

from modes.socratic.problems import Problem

__all__ = ["fraction_predictions", "percentage_predictions"]

_PERCENTAGE = re.compile(r"(\d+(?:\.\d+)?)% de (\d+(?:\.\d+)?)")
_TWO_FRACTIONS = re.compile(
    r"(?P<a>\d+)\s*/\s*(?P<b>\d+) (?P<sign>[+-]) (?P<c>\d+)\s*/\s*(?P<d>\d+)"
)


def percentage_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """p% de n: the child multiplied the percent by n, or subtracted it from n."""
    match = _PERCENTAGE.fullmatch(problem.text)
    if match is None:
        return []
    percent, base = Fraction(match.group(1)), Fraction(match.group(2))
    return [
        ("multiplied_by_percentage_directly", percent * base),
        ("subtracted_percentage_as_raw_number", base - percent),
    ]


def fraction_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """a/b + c/d or a/b - c/d: the child combined the denominators as well."""
    match = _TWO_FRACTIONS.fullmatch(problem.text.replace(",", ""))  # 1,000/3 + 1/2
    if match is None:
        return []
    a, b, c, d = (int(match[letter]) for letter in "abcd")
    if match["sign"] == "+":
        return [("added_denominators", Fraction(a + c, b + d))]
    # With equal denominators the difference would divide by zero: no prediction.
    return [("subtracted_denominators", None if b == d else Fraction(a - c, b - d))]
