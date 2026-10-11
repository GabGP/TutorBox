"""Misconceptions in whole-number arithmetic and in the order of operations.

Each function returns (misconception slug, the wrong value that mistake gives), in
the order the classifier tries them. A rule that does not apply to the problem gives
None as its value, which equals no attempt.
"""

import operator
import re
from collections.abc import Callable
from fractions import Fraction

from core.math_engine import evaluate_exact
from modes.socratic.problems import Problem

__all__ = [
    "addition_predictions",
    "division_predictions",
    "expression_predictions",
    "multiplication_predictions",
    "subtraction_predictions",
]

_TIMES_TABLE_LIMIT = 12
_WITHOUT_PARENTHESES = str.maketrans("", "", "()")
_CHAIN = re.compile(r"\d+(?:\s*[+\-×÷]\s*\d+)+")  # numbers joined by operators
_TOKEN = re.compile(r"\d+|[+\-×÷]")
_APPLY = {
    "+": operator.add,
    "-": operator.sub,
    "×": operator.mul,
    "÷": operator.truediv,
}


def addition_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """Suma: the digits were not lined up, so 23 + 5 was worked out as 23 + 50."""
    if len(problem.operands) != 2:
        return []
    first, second = problem.operands
    return [("alignment_error", _misaligned(first, second, operator.add))]


def subtraction_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """Resta: the child added, borrowed wrongly column by column, or misaligned."""
    if len(problem.operands) != 2:
        return []
    first, second = problem.operands
    return [
        ("added_instead_of_subtracted", Fraction(first + second)),
        ("borrowing_error", Fraction(_column_differences(first, second))),
        ("alignment_error", _misaligned(first, second, operator.sub)),
    ]


def multiplication_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """Multiplicacion: a neighbour in the times table, one group too many or few."""
    if len(problem.operands) != 2:
        return []
    first, second = problem.operands
    if not (1 <= first <= _TIMES_TABLE_LIMIT and 1 <= second <= _TIMES_TABLE_LIMIT):
        return []
    neighbours = (
        first * (second - 1),
        first * (second + 1),
        (first - 1) * second,
        (first + 1) * second,
    )
    return [("table_lookup_error", Fraction(value)) for value in neighbours]


def division_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """Division: the child divided the other way round (12 ÷ 4 worked as 4 ÷ 12)."""
    if len(problem.operands) != 2:
        return []
    dividend, divisor = problem.operands
    if dividend == 0:
        return []
    return [("inverted_division", Fraction(divisor, dividend))]


def expression_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """Combinada: the child dropped the parentheses, or read the operators in order."""
    text = problem.text.replace(",", "")  # thousands commas: 1,000 + 2
    if "(" in text or ")" in text:
        ignoring_parentheses = evaluate_exact(text.translate(_WITHOUT_PARENTHESES))
        return [("ignored_parentheses", ignoring_parentheses)]
    return [("left_to_right_precedence", _left_to_right(text))]


def _left_to_right(expression: str) -> Fraction | None:
    """2 + 3 × 4 read strictly left to right is 20; None if it cannot be read so."""
    if _CHAIN.fullmatch(expression) is None:
        return None
    tokens = _TOKEN.findall(expression)
    value = Fraction(tokens[0])
    for symbol, operand_text in zip(tokens[1::2], tokens[2::2]):
        operand = Fraction(operand_text)
        if symbol == "÷" and operand == 0:
            return None
        value = _APPLY[symbol](value, operand)
    return value


def _misaligned(
    first: int, second: int, operation: Callable[[int, int], int]
) -> Fraction | None:
    """The result with the shorter number one place further left (23 + 5 as 23 + 50).

    None when both numbers have the same number of digits: nothing is misaligned.
    """
    # How many more digits the first number has than the second.
    gap = len(str(first)) - len(str(second))
    if gap < 0:
        return Fraction(operation(first * 10**-gap, second))
    if gap > 0:
        return Fraction(operation(first, second * 10**gap))
    return None


def _column_differences(first: int, second: int) -> int:
    """52 - 17 column by column: |5 - 1| and |2 - 7| make 45 (digits right-aligned)."""
    width = max(len(str(first)), len(str(second)))
    columns = zip(str(first).zfill(width), str(second).zfill(width))
    return int("".join(str(abs(int(top) - int(bottom))) for top, bottom in columns))
