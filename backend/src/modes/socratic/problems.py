"""Finds the math problem in a child's message and computes its answer exactly.

Operations can be written with symbols or words ("7 por 8", "12 entre 4",
"5 más 3"). A lone fraction such as 3/4 is a number, not a problem: a problem
needs +, -, × or ÷. The answer (target) is never shown until the child finds it.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

from core.math_engine import evaluate_exact, solve_linear_equation
from modes.socratic.numbers import extract_numbers
from modes.socratic.text import fold

__all__ = ["Problem", "accepted_answers", "find_attempt", "find_problem", "normalize"]

_MAX_EXPRESSION_CHARS = 60
_MAX_OPERAND = 10**9
_OPERATORS = (
    (re.compile(r"(?<=\d)\s*(?:multiplicado por|por|x|×|·|\*)\s*(?=\d)"), " × "),
    (re.compile(r"(?<=\d)\s*(?:dividido (?:entre|por)|entre|÷)\s*(?=\d)"), " ÷ "),
    (re.compile(r"(?<=\d)\s*(?:mas|\+)\s*(?=\d)"), " + "),
    (re.compile(r"(?<=\d)\s*(?:menos|[-−–])\s*(?=\d)"), " - "),
)
_WORDED = (  # "el doble de 8" is 8 × 2
    (re.compile(r"\b(?:el )?doble de (\d+)"), r"\1 × 2"),
    (re.compile(r"\b(?:el )?triple de (\d+)"), r"\1 × 3"),
    (re.compile(r"\b(?:la )?mitad de (\d+)"), r"\1 ÷ 2"),
    (re.compile(r"\b(?:la )?(?:cuarta parte|cuarto) de (\d+)"), r"\1 ÷ 4"),
)
_EXPRESSION = re.compile(r"\(?\d[\d\s+\-×÷/().]*[\d)]")
_BINARY = re.compile(r"(\d+) ([+\-×÷]) (\d+)")
_BIG = re.compile(r"(?<![\d.])\d{4,}(?![\d.])")
_OPERATION_NAMES = {"+": "suma", "-": "resta", "×": "multiplicacion", "÷": "division"}
_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*de\s*(\d+(?:\.\d+)?)")
# The unknown of a 4th/5th grade "operación abierta": __ × 32 = 192, x + 5 = 12.
_UNKNOWN = re.compile(r"_+|□|\?|(?<![a-z])[xn](?![a-z])")
_EQUATION = re.compile(
    r"(?<![a-z])[\d(_□?xn][\d\s+\-×÷/()._□?xn]*=\s*\d+(?:\.\d+)?(?![\d.])"
)


@dataclass(frozen=True)
class Problem:
    """A problem the child asked about, e.g. text '23 + 45' and target 68."""

    text: str
    target: Fraction
    operation: str
    operands: tuple[int, ...] = ()
    decimal: bool = False


def accepted_answers(problem: Problem) -> frozenset[Fraction]:
    """The target, plus the whole quotient of a division with remainder (17 ÷ 5 → 3)."""
    target = problem.target
    if problem.operation == "division" and target.denominator != 1:
        return frozenset({target, Fraction(target.numerator // target.denominator)})
    return frozenset({target})


def normalize(text: str) -> str:
    """Folds accents and writes operations as ' + ', ' - ', ' × ', ' ÷ '."""
    normalized = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", fold(text))
    normalized = re.sub(r"(\d),(\d)", r"\1.\2", normalized)
    for pattern, symbol in _WORDED + _OPERATORS:
        normalized = pattern.sub(symbol, normalized)
    return re.sub(r"\s+", " ", normalized)


def find_problem(message: str) -> Problem | None:
    """The problem in the message: a percentage, an equation or an operation."""
    text = normalize(message)
    if match := _PERCENT.search(text):
        percent, base = Fraction(match.group(1)), Fraction(match.group(2))
        shown = f"{match.group(1)}% de {match.group(2)}"
        return Problem(shown, percent * base / 100, "porcentaje")
    left, equals, right = text.partition("=")
    if not equals:
        return _operation(text)
    asked = right.strip(" .¿")
    if asked == "" or _UNKNOWN.fullmatch(asked) or not _UNKNOWN.search(left):
        return _operation(left)  # "3 × 4 = ?" or "23 + 45 = 70": the left side
    return _equation(text)


def find_attempt(message: str) -> tuple[Problem, Fraction] | None:
    """'23 + 45 = 70': the child's own result for an operation, to be judged."""
    left, equals, right = normalize(message).partition("=")
    values = extract_numbers(right)
    if not equals or len(values) != 1 or _UNKNOWN.search(left):
        return None
    problem = _operation(left)
    return (problem, values[0]) if problem is not None else None


def _equation(text: str) -> Problem | None:
    match = _EQUATION.search(text)
    if match is None or len(match.group(0)) > _MAX_EXPRESSION_CHARS:
        return None
    shown = match.group(0).strip()
    if "××" in shown:  # Python would read it as a power; the tutor has none
        return None
    equation = _UNKNOWN.sub("x", shown).replace("×", "*").replace("÷", "/")
    solution = solve_linear_equation(equation)
    if solution is None or not solution.is_Rational:
        return None
    return Problem(shown, Fraction(int(solution.p), int(solution.q)), "ecuacion")


def _operation(text: str) -> Problem | None:
    candidates = [m.group(0).strip() for m in _EXPRESSION.finditer(text)]
    for expression in sorted(candidates, key=len, reverse=True):
        if not any(op in expression for op in "+-×÷"):
            continue
        target = _evaluate(expression)
        if target is None:
            return None
        shown = _BIG.sub(lambda m: f"{int(m.group(0)):,}", expression)
        return Problem(shown, target, *_classify(expression))
    return None


def _evaluate(expression: str) -> Fraction | None:
    too_big = any(abs(n) > _MAX_OPERAND for n in extract_numbers(expression))
    if too_big or len(expression) > _MAX_EXPRESSION_CHARS:
        return None
    return evaluate_exact(expression)


def _classify(expression: str) -> tuple[str, tuple[int, ...], bool]:
    decimal = "." in expression
    if match := _BINARY.fullmatch(expression):
        operands = (int(match.group(1)), int(match.group(3)))
        return _OPERATION_NAMES[match.group(2)], operands, decimal
    if "/" in expression:
        return "fracciones", (), decimal
    return ("decimales" if decimal else "combinada"), (), decimal
