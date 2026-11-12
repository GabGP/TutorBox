"""The misconception behind a wrong answer picks the tutor's question."""

import pytest

from modes.socratic import hints, misconception_hints
from modes.socratic.containment import leaks
from modes.socratic.misconception_hints import misconception_hint
from modes.socratic.planner import plan
from modes.socratic.problems import find_problem
from modes.socratic.state import Conversation
from modes.socratic.telemetry import UNCLASSIFIED
from tests.conftest import required
from tests.modes.socratic.telemetry.test_error_type import LABELLED

pytestmark = pytest.mark.usefixtures("first_wording")  # pins exact texts


@pytest.mark.parametrize(("text", "attempt", "slug"), LABELLED)
def test_the_question_names_the_problem_and_never_its_answer(text, attempt, slug):
    problem = required(find_problem(text))

    question = misconception_hint(problem, slug)

    if question is not None:  # None is the containment fallback to the ladder
        assert problem.text in question
        assert "?" in question
        assert not leaks(question, problem)


def test_a_borrowing_error_and_another_wrong_answer_get_different_hints():
    working = plan(Conversation(), "52 - 17")[1]

    borrowed, after = plan(working, "45")
    other, _ = plan(working, "60")

    assert (borrowed.kind, borrowed.level, after.error) == (
        "hint",
        1,
        "borrowing_error",
    )
    assert "prestada" in borrowed.text
    assert other.text.endswith(hints.hint(required(working.problem), 1))


def test_the_same_misconception_again_climbs_the_ladder():
    working = plan(Conversation(), "52 - 17")[1]
    _, after = plan(working, "45")

    move, _ = plan(after, "45")

    assert move.level == 2
    assert move.text.endswith(hints.hint(required(working.problem), 2))


def test_no_question_for_an_unclassified_answer_or_one_that_would_leak(monkeypatch):
    problem = required(find_problem("52 - 17"))
    assert misconception_hint(problem, UNCLASSIFIED) is None

    monkeypatch.setattr(misconception_hints, "leaks", lambda text, problem: True)

    assert misconception_hint(problem, "borrowing_error") is None
