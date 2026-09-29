"""The tutor's deterministic decisions for each message (planner.py)."""

import pytest

from modes.socratic import replies
from modes.socratic.planner import MAX_LEVEL, plan
from modes.socratic.state import Conversation


def _working_on(message: str) -> Conversation:
    return plan(Conversation(), message)[1]


def test_a_new_problem_starts_the_ladder_at_level_0():
    move, conversation = plan(Conversation(), "¿cuánto es 23 + 45?")

    assert (move.kind, move.llm, move.level) == ("hint", "rewrite", 0)
    assert conversation.problem.text == "23 + 45"
    assert conversation.level == 0


def test_wrong_answers_climb_the_ladder_up_to_level_3():
    conversation = _working_on("23 + 45")

    for expected in (1, 2, 3, MAX_LEVEL):
        move, conversation = plan(conversation, "70")
        assert (move.kind, move.level, move.is_correct) == ("hint", expected, False)
        assert move.text.startswith("Todavía no.")


def test_the_right_answer_is_praised_and_clears_the_problem():
    move, conversation = plan(_working_on("23 + 45"), "creo que es 68")

    assert (move.kind, move.llm, move.is_correct) == ("praise", "none", True)
    assert conversation == Conversation()


def test_asking_for_help_climbs_the_ladder():
    move, conversation = plan(_working_on("7 por 8"), "no sé, ayúdame")
    assert (move.kind, move.level) == ("hint", 1)

    move, conversation = plan(conversation, "ok")  # short replies count as help
    assert move.level == 2


def test_an_attempt_with_equals_is_judged_on_its_own_problem():
    move, conversation = plan(Conversation(), "23 + 45 = 70")
    assert (move.kind, move.level, move.is_correct) == ("hint", 1, False)

    move, _ = plan(conversation, "23 + 45 = 68")  # same problem keeps its level
    assert (move.kind, move.level) == ("praise", 1)


def test_off_topic_during_a_problem_brings_the_child_back():
    conversation = _working_on("7 por 8")

    move, after = plan(conversation, "tengo 8 años y me gusta jugar fútbol")

    assert move.text == replies.back_to(conversation.problem)
    assert after == conversation


@pytest.mark.parametrize(
    ("message", "kind"),
    [
        ("", "input"),
        ("<img src=tarea.png>", "input"),
        ("¿cómo se hace una derivada?", "beyond"),
        ("¿quién ganó el mundial?", "off_topic"),
        ("hola", "social"),
        ("5 - 8", "negative"),
        ("5 - 8 = 3", "negative"),
        ("68", "orphan"),
    ],
)
def test_deterministic_moves(message, kind):
    move, conversation = plan(Conversation(), message)

    assert (move.kind, move.llm) == (kind, "none")
    assert conversation == Conversation()


def test_a_word_problem_asks_for_the_operation_then_for_the_work():
    move, conversation = plan(
        Conversation(), "tengo 5 manzanas y me dan 3, ¿cuántas tengo?"
    )
    assert (move.kind, move.llm) == ("word_problem", "rewrite")
    assert conversation.word_numbers == (5, 3)

    move, _ = plan(conversation, "8")
    assert move.kind == "show_work"


@pytest.mark.parametrize(
    ("question", "reply"),
    [
        ("¿qué es una fracción?", "creo que es 3/4"),
        ("¿cuántos lados tiene un triángulo?", "tiene tres"),
    ],
)
def test_the_childs_idea_after_an_explanation_is_welcomed(question, reply):
    after_explaining = plan(Conversation(), question)[1]

    move, conversation = plan(after_explaining, reply)

    assert move.kind == "idea"
    assert move.text.startswith("¡Gracias por tu idea!")
    assert conversation == Conversation()


def test_a_new_question_after_an_explanation_is_not_an_idea():
    after_explaining = plan(Conversation(), "¿qué es una fracción?")[1]

    move, _ = plan(after_explaining, "¿quién ganó el mundial?")

    assert move.kind == "off_topic"


@pytest.mark.parametrize(
    ("message", "kind", "llm", "topic_id"),
    [
        ("¿qué es una fracción?", "explain", "explain", "fracciones"),
        ("¿cuántos lados tiene un triángulo?", "think", "rewrite", "geometria"),
        ("¿qué es 3/4?", "explain", "explain", "fracciones"),
        ("¿qué significa 1,000?", "explain", "explain", "numeracion"),
    ],
)
def test_concept_questions(message, kind, llm, topic_id):
    move, _ = plan(Conversation(), message)

    assert (move.kind, move.llm, move.topic.id) == (kind, llm, topic_id)
    assert move.question == (message if kind == "explain" else "")
