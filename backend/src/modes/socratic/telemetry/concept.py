"""The CURRICULUM_TAXONOMY concept and the CNB topic that a tutor turn practises.

A turn with a problem gets its concept from the problem's operation; a concept
question (no problem) gets it from its CNB topic id alone. The taxonomy strings
are literals here, not imports from the quiz; the tests check them against it.
"""

from dataclasses import dataclass

from core.math_engine import extract_linear_polynomial, is_two_step_linear
from modes.socratic.problems import Problem, sympy_equation

__all__ = ["Concept", "concept_for"]

_CNB_FRACTIONS = "fracciones"
_CNB_EQUATIONS = "operaciones_combinadas"
# find_problem writes operations as spaced signs (normalize in problems.py).
_ADDITIVE_SIGNS = (" + ", " - ")
_MULTIPLICATIVE_SIGNS = (" × ", " ÷ ")


@dataclass(frozen=True)
class Concept:
    """What a turn practises; a field is None when the turn does not name it."""

    topic: str | None = None  # CURRICULUM_TAXONOMY topic
    subconcept: str | None = None  # CURRICULUM_TAXONOMY subconcept
    cnb_topic: str | None = None  # cnb_matematicas.json topic id


# Problem.decimal needs no override: find_problem sets it only on "decimales" and
# "fracciones" problems, never on suma, resta, multiplicacion or division.
_CONCEPT_BY_OPERATION: dict[str, Concept] = {
    "suma": Concept("arithmetic", "addition_subtraction", "suma_resta"),
    "resta": Concept("arithmetic", "addition_subtraction", "suma_resta"),
    "multiplicacion": Concept(
        "arithmetic", "multiplication_division", "multiplicacion"
    ),
    "division": Concept("arithmetic", "multiplication_division", "division"),
    "combinada": Concept("arithmetic", "order_of_operations", "operaciones_combinadas"),
    "decimales": Concept("decimals_percentages", "decimal_operations", "decimales"),
    "porcentaje": Concept("decimals_percentages", "percentages", "razones_porcentajes"),
}

_TOPIC_ID_CONCEPTS: dict[str, tuple[str, str | None]] = {
    "suma_resta": ("arithmetic", "addition_subtraction"),
    "multiplicacion": ("arithmetic", "multiplication_division"),
    "division": ("arithmetic", "multiplication_division"),
    "operaciones_combinadas": ("arithmetic", "order_of_operations"),
    "fracciones": ("fractions", None),
    "decimales": ("decimals_percentages", "decimal_operations"),
    "razones_porcentajes": ("decimals_percentages", "percentages"),
}


def concept_for(problem: Problem | None, topic_id: str | None) -> Concept:
    """The problem's concept when the turn has a problem, else its topic id's."""
    if problem is not None:
        return _concept_for_problem(problem)
    if topic_id is not None:
        return _concept_for_topic_id(topic_id)
    return Concept()


def _concept_for_problem(problem: Problem) -> Concept:
    if problem.operation == "fracciones":
        subconcept = _fraction_subconcept(problem.text)
        return Concept("fractions", subconcept, _CNB_FRACTIONS)
    if problem.operation == "ecuacion":
        subconcept = _equation_subconcept(problem.text)
        return Concept("pre_algebra", subconcept, _CNB_EQUATIONS)
    # An operation the tutor adds later is logged without a concept, not an error.
    return _CONCEPT_BY_OPERATION.get(problem.operation, Concept())


def _fraction_subconcept(text: str) -> str | None:
    """Named by its signs only: the '/' of a fraction is not a sign."""
    has_additive = any(sign in text for sign in _ADDITIVE_SIGNS)
    has_multiplicative = any(sign in text for sign in _MULTIPLICATIVE_SIGNS)
    if has_additive and not has_multiplicative:
        return "addition_subtraction"
    if has_multiplicative and not has_additive:
        return "multiplication_division"
    return None  # a mix of both kinds, or no spaced sign at all


def _equation_subconcept(text: str) -> str | None:
    """Two-step when the variable side is ax + b, with a not in {-1, 0, 1}, b != 0."""
    found = extract_linear_polynomial(sympy_equation(text))
    if found is None:  # the variable side is not a polynomial, e.g. 1 ÷ x
        return None
    polynomial, _variable = found
    if is_two_step_linear(polynomial):
        return "two_step_equations"
    return "one_step_equations"


def _concept_for_topic_id(topic_id: str) -> Concept:
    topic, subconcept = _TOPIC_ID_CONCEPTS.get(topic_id, (None, None))
    return Concept(topic, subconcept, topic_id)
