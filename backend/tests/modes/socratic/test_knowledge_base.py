"""The tutor's knowledge base: every pre-written text is proven in CI (knowledge.py).

An explanation must pass the guard a model reply passes, end with a question and
state only true equalities; a misconception question must name a slug the
classifier returns and carry no number of its own. Mid-problem, an explanation
never gives the answer away.
"""

import re
from fractions import Fraction

import pytest

from core.math_engine import evaluate_exact
from modes.quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from modes.socratic import hints, replies
from modes.socratic.containment import leaks
from modes.socratic.curriculum import load_curriculum
from modes.socratic.guard import check
from modes.socratic.knowledge import (
    explanations,
    load_knowledge,
    misconception_question,
    variant,
)
from modes.socratic.numbers import digits_for_words, extract_numbers
from modes.socratic.planner import plan
from modes.socratic.problems import find_problem
from modes.socratic.state import Conversation
from modes.socratic.telemetry import ERROR_SLUGS
from tests.conftest import required

KNOWLEDGE = load_knowledge()
TOPICS = load_curriculum().topics
EXPLANATIONS = [
    (topic_id, text)
    for topic_id, texts in KNOWLEDGE["explanations"].items()
    for text in texts
]
MISCONCEPTIONS = [
    (slug, question)
    for slug, questions in KNOWLEDGE["misconceptions"].items()
    for question in questions
]
NUMBER = r"\d+(?:[./]\d+)?"
# A written equality between numbers: '3 + 4 = 7', '1/4 + 2/4 = 3/4'.
EQUALITY = re.compile(rf"({NUMBER}(?:\s*[+\-×÷]\s*{NUMBER})+)\s*=\s*({NUMBER})")


def _false_equalities(text: str) -> list[str]:
    return [
        f"{left} = {right}"
        for left, right in EQUALITY.findall(text)
        if evaluate_exact(left) != Fraction(right)
    ]


def test_every_cnb_topic_has_two_or_three_distinct_explanations():
    assert set(KNOWLEDGE["explanations"]) == {topic.id for topic in TOPICS}
    for topic in TOPICS:
        texts = explanations(topic.id)
        assert 2 <= len(set(texts)) == len(texts) <= 3, topic.id


@pytest.mark.parametrize(("topic_id", "text"), EXPLANATIONS)
def test_an_explanation_passes_the_output_guard_and_ends_with_a_question(
    topic_id, text
):
    assert check(text, mode="explain", source="", problem=None) == []
    assert text.endswith("?")


@pytest.mark.parametrize(("topic_id", "text"), EXPLANATIONS)
def test_every_equality_an_explanation_writes_is_true(topic_id, text):
    assert _false_equalities(text) == []


def test_the_equality_check_reads_the_explanations_and_catches_a_false_one():
    written = [found for _, text in EXPLANATIONS for found in EQUALITY.findall(text)]

    assert ("1/4 + 2/4", "3/4") in written
    assert _false_equalities("Mira: 3 + 4 = 8 y 2 × 5 = 10.") == ["3 + 4 = 8"]


def test_every_misconception_the_classifier_names_has_a_question():
    taxonomy_slugs = {
        slug
        for subconcepts in CURRICULUM_TAXONOMY.values()
        for slugs in subconcepts.values()
        for slug in slugs
    }

    assert ERROR_SLUGS <= set(KNOWLEDGE["misconceptions"]) <= taxonomy_slugs


@pytest.mark.parametrize(("slug", "question"), MISCONCEPTIONS)
def test_a_misconception_question_names_the_problem_and_no_number(slug, question):
    assert "{p}" in question
    assert "?" in question
    assert not re.search(r"\d", question)
    assert re.findall(r"\{(\w*)\}", question) == ["p"]
    assert question in KNOWLEDGE["misconceptions"][slug]


def test_every_misconception_has_five_distinct_questions_and_the_problem_picks_one():
    for slug, questions in KNOWLEDGE["misconceptions"].items():
        assert len(set(questions)) == len(questions) == 5, slug
        picked = {misconception_question(slug, f"{n} + 1") for n in range(60)}
        assert picked == set(questions), slug
        assert misconception_question(slug, "7 + 8") == misconception_question(
            slug, "7 + 8"
        )


def test_the_not_yet_opener_has_five_to_eight_one_sentence_wordings_without_numbers():
    wordings = KNOWLEDGE["paraphrases"]["not_yet"]  # hint templates: test_hint_wordings
    assert 5 <= len(set(wordings)) == len(wordings) <= 8
    assert not any(extract_numbers(digits_for_words(text)) for text in wordings)
    # One sentence each: the output guard keeps three sentences of a rewording.
    assert all(re.fullmatch(r"[^.!?]+\.", text) for text in wordings)
    assert {variant("not_yet", seed) for seed in range(len(wordings))} == set(wordings)


def test_a_wrong_answer_opens_with_a_not_yet_wording_that_varies_with_the_attempt():
    working = plan(Conversation(), "23 + 45")[1]
    clue = hints.hint(required(working.problem), 1)
    openers = set()

    for attempt in range(60, 66):
        move, _ = plan(working, str(attempt))
        assert move.text.endswith(f" {clue}")
        openers.add(move.text.removesuffix(f" {clue}"))

    assert openers == set(KNOWLEDGE["paraphrases"]["not_yet"])


def test_an_unknown_key_has_no_knowledge():
    assert explanations("astronomia") == ()
    assert misconception_question("unclassified", "3 + 4") is None


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
def test_the_question_picks_among_the_topics_explanations(topic):
    texts = explanations(topic.id)

    picked = {replies.explain_fallback(topic, "x" * size) for size in range(6)}

    assert picked == set(texts)


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("working_on", ["3 + 4", "9 - 4", "3 × 4", "20 ÷ 5"])
def test_an_explanation_never_gives_the_problem_in_progress_away(topic, working_on):
    active = required(find_problem(working_on))

    for size in range(3):
        text = replies.explain_fallback(topic, "x" * size, active)
        assert not leaks(text, active)


def test_with_no_safe_explanation_the_child_is_invited_to_share(monkeypatch):
    topic = required(load_curriculum().get("fracciones"))
    monkeypatch.setattr(replies, "leaks", lambda text, problem: True)

    text = replies.explain_fallback(topic, "", required(find_problem("3 + 4")))

    assert text.startswith("Hablemos de fracciones.")


def test_a_concept_question_mid_problem_gets_an_explanation_that_keeps_the_answer():
    working = plan(Conversation(), "3 + 4")[1]
    problem = required(working.problem)

    move, after = plan(working, "¿qué es una suma?")

    assert (move.kind, after.problem) == ("explain", problem)
    assert move.text in explanations("suma_resta")
    assert not leaks(move.text, problem)
