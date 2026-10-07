"""The labeled problem bank: >= 40 problems, each one proven in CI (bank.py).

SymPy solves every problem from its expression and checks its structure against
its labels (the quiz's validators); the tutor must read the child's text to the
same answer, give four distinct hints that never leak it, and climb 0 → 3 and
stay there on wrong answers.
"""

import json
from collections import Counter
from pathlib import Path

import pytest
import sympy as sp

from core.math_engine import extract_and_solve_problem, validate_math_structure
from modes.quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from modes.socratic import hints
from modes.socratic.bank import load_bank
from modes.socratic.containment import leaks
from modes.socratic.curriculum import load_curriculum
from modes.socratic.planner import MAX_LEVEL, plan
from modes.socratic.problems import find_problem
from modes.socratic.state import Conversation

BANK = load_bank()
OPERATIONS = {
    "addition_subtraction": {"suma", "resta"},
    "multiplication_division": {"multiplicacion", "division"},
    "one_step_equations": {"ecuacion"},
    "two_step_equations": {"ecuacion"},
}


def _ids(item):
    return item.id


def test_the_bank_has_at_least_40_distinct_arithmetic_and_pre_algebra_problems():
    assert len(BANK) >= 40
    for field in ("id", "text", "expression"):
        assert len({getattr(item, field) for item in BANK}) == len(BANK), field
    per_subconcept = Counter(item.subconcept for item in BANK)
    assert set(per_subconcept) == set(OPERATIONS)
    assert min(per_subconcept.values()) >= 10


def test_an_unknown_field_is_rejected(tmp_path: Path):
    entry = {**vars(BANK[0]), "answer": 12, "nivel": 1}  # a typo'd label
    bad = tmp_path / "bank.json"
    bad.write_text(json.dumps({"problems": [entry]}), encoding="utf-8")

    with pytest.raises(TypeError):
        load_bank.__wrapped__(bad)


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_labels_name_a_quiz_concept_and_a_cnb_grade(item):
    assert item.subconcept in CURRICULUM_TAXONOMY[item.topic]
    assert item.grade in load_curriculum().get(item.cnb).grades
    assert item.answer >= 0 and item.answer.denominator == 1


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_sympy_proves_the_answer_and_the_structure(item):
    solution, mode = extract_and_solve_problem(item.expression)

    assert solution == sp.Rational(item.answer.numerator, item.answer.denominator)
    assert (
        validate_math_structure(item.expression, item.topic, item.subconcept, mode)
        == []
    )


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_the_tutor_reads_the_childs_text_to_the_same_answer(item):
    problem = find_problem(item.text)

    assert problem.target == item.answer
    assert problem.operation in OPERATIONS[item.subconcept]


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_four_distinct_hints_that_ask_and_never_leak(item):
    problem = find_problem(item.text)
    ladder = [hints.hint(problem, level) for level in range(MAX_LEVEL + 1)]

    assert len(set(ladder)) == 4
    assert all("?" in text for text in ladder)
    assert not any(leaks(text, problem) for text in ladder)
    # every problem gets a real smaller step and a worked example
    assert ladder[2] != hints._generic(problem.text, 2)
    assert ladder[3] != hints._generic(problem.text, 3)


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_wrong_answers_climb_to_level_3_and_stay_there_until_solved(item):
    move, conversation = plan(Conversation(), item.text)
    levels = [move.level]
    for _ in range(5):
        move, conversation = plan(conversation, str(item.answer + 1))
        levels.append(move.level)

    assert levels == [0, 1, 2, 3, 3, 3]
    assert plan(conversation, str(item.answer))[0].kind == "praise"
