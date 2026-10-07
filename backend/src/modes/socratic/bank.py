"""The tutor's labeled problem bank (problem_bank.json), validated in CI.

Arithmetic and pre-algebra problems for 1.º to 5.º primaria. Each one carries the
text a child would type, the same problem as SymPy reads it, its answer, the
quiz's CURRICULUM_TAXONOMY topic and subconcept (so tutor turns share the error
report's concepts) and its CNB grade and topic. test_problem_bank.py proves every
answer with SymPy and walks every problem up the hint ladder through containment.
"""

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

__all__ = ["BankProblem", "load_bank"]

_DATA_FILE = Path(__file__).with_name("problem_bank.json")


@dataclass(frozen=True)
class BankProblem:
    id: str
    text: str  # as a child would write it
    expression: str  # the same problem as SymPy reads it
    answer: Fraction
    topic: str  # CURRICULUM_TAXONOMY topic, shared with the quiz
    subconcept: str
    grade: int  # CNB primaria grade
    cnb: str  # cnb_matematicas.json topic id


@lru_cache(maxsize=1)
def load_bank(path: Path = _DATA_FILE) -> tuple[BankProblem, ...]:
    """Parses the bank once per process; an unknown field is an error."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        BankProblem(**{**entry, "answer": Fraction(entry["answer"])})
        for entry in data["problems"]
    )
