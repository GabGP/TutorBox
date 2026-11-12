"""Every hint template has five wordings (knowledge_base.json); each is proven here.

A wording keeps the placeholders, the question and the sentence count of the first
one (the text the code used to hold), adds no number of its own and passes the
output guard. Walking all five (the `wording` fixture forces the index) shows that
whichever one a problem's seed picks, the hints never leak and still climb 0 to 3.
"""

import re
import zlib
from fractions import Fraction
from string import Formatter

import pytest

from modes.socratic import hints, replies
from modes.socratic.bank import load_bank
from modes.socratic.containment import leaks
from modes.socratic.curriculum import load_curriculum
from modes.socratic.guard import check
from modes.socratic.knowledge import load_knowledge, seed_of
from modes.socratic.misconception_hints import misconception_hint
from modes.socratic.numbers import digits_for_words, extract_numbers
from modes.socratic.problems import find_problem
from tests.conftest import required

KNOWLEDGE = load_knowledge()
TEMPLATES = {k: v for k, v in KNOWLEDGE["paraphrases"].items() if k != "not_yet"}
BANK = load_bank()
SAMPLE = {  # the longest values a template meets
    "p": "24 ÷ 6 + 3 × 2",
    "title": "perímetro y área",
    "listed": "5 y 3 y 12 y 8",
    "sums": "3 + 3 + 3 + 3 + 3",
    "u": "x",
}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
CONCEPTS = ("1/2 + 1/4", "0.5 + 0.25", "20% de 50", "2 + 3 × 4 - 1")
EQUATIONS = (
    "x + 5 = 12",
    "n - 7 = 9",
    "3 × __ = 24",
    "x ÷ 4 = 6",
    "2x + 4 = 14",
    "5n - 3 = 27",
)


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in Formatter().parse(text) if name}


def _literal(text: str) -> str:
    return "".join(literal for literal, *_ in Formatter().parse(text))


def _filled(text: str) -> str:
    return text.format_map({name: SAMPLE.get(name, "48") for name in _fields(text)})


def _echo_is_safe(text: str, problem=None) -> bool:
    return check(text, mode="rewrite", source=text, problem=problem) == []


def _numbers(text: str) -> set:
    return set(extract_numbers(digits_for_words(_literal(text))))


def test_there_is_one_key_per_hint_template():
    assert len(TEMPLATES) == 43
    assert {
        "resta_2_borrow",
        "word_problem",
        "think_first",
        "eq_worked_cociente",
    } <= set(TEMPLATES)


@pytest.mark.parametrize("key", TEMPLATES)
def test_a_template_has_five_distinct_wordings_with_the_same_placeholders(key):
    first = TEMPLATES[key][0]

    assert len(TEMPLATES[key]) == len(set(TEMPLATES[key])) == 5
    for text in TEMPLATES[key]:
        assert _fields(text) == _fields(first)
        assert "?" in text
        assert _numbers(text) <= _numbers(first)  # a table's 1 and 2, a 100
        assert len(SENTENCE_END.split(_filled(text))) <= len(
            SENTENCE_END.split(_filled(first))
        )


@pytest.mark.parametrize("key", TEMPLATES)
def test_every_wording_passes_the_output_guard_at_its_longest(key):
    for text in map(_filled, TEMPLATES[key]):
        assert _echo_is_safe(text), text


def test_every_misconception_question_passes_the_output_guard():
    for questions in KNOWLEDGE["misconceptions"].values():
        for text in questions:
            assert _echo_is_safe(text.format(p=SAMPLE["p"])), text


def test_the_seed_is_stable_across_processes_and_a_hint_is_a_pure_function():
    assert seed_of("23 + 45") == zlib.crc32(b"23 + 45")
    for item in BANK:
        problem = required(find_problem(item.text))
        for level in range(4):
            assert hints.hint(problem, level) == hints.hint(problem, level)


def test_different_problems_get_different_wordings():
    problems = [required(find_problem(item.text)) for item in BANK]

    assert len({hints.hint(problem, 0) for problem in problems}) >= 30
    assert {seed_of(problem.text) % 5 for problem in problems} == set(range(5))


def test_every_wording_of_every_bank_hint_never_leaks_and_the_echo_passes(wording):
    for item in BANK:
        problem = required(find_problem(item.text))
        ladder = [hints.hint(problem, level) for level in range(4)]

        assert len(set(ladder)) == 4, item.id
        assert not any(leaks(text, problem) for text in ladder), item.id
        assert all("?" in text and _echo_is_safe(text, problem) for text in ladder)
        # a real smaller step and worked example, not the generic fallback
        assert ladder[2] != hints._generic(problem.text, 2), item.id
        assert ladder[3] != hints._generic(problem.text, 3), item.id


@pytest.mark.parametrize("text", CONCEPTS)
def test_every_wording_of_a_concept_hint_asks_and_passes(wording, text):
    problem = required(find_problem(text))

    for level in range(4):  # levels 0, 2 and 3 are the generic wordings here
        said = hints.hint(problem, level)
        assert "?" in said and not leaks(said, problem)
        assert _echo_is_safe(said, problem), said
    assert hints.hint(problem, 1) != hints._generic(problem.text, 1)


@pytest.mark.parametrize("text", EQUATIONS)
def test_every_wording_of_an_equation_hint_never_leaks(wording, text):
    problem = required(find_problem(text))

    for level in (2, 3):
        said = hints.hint(problem, level)
        assert said != hints._generic(problem.text, level)
        assert not leaks(said, problem) and _echo_is_safe(said, problem), said


def test_every_wording_of_a_misconception_question_never_leaks(wording):
    asked = 0
    for item in BANK:
        problem = required(find_problem(item.text))
        for slug in KNOWLEDGE["misconceptions"]:
            question = misconception_hint(problem, slug)
            if question is not None:  # None is the fallback to the ladder
                asked += 1
                assert "?" in question and _echo_is_safe(question, problem)
    assert asked > 400


def test_every_wording_of_the_replies_passes_the_guard(wording):
    for numbers in (
        [Fraction(5), Fraction(3)],
        [Fraction(12), Fraction(8), Fraction(2)],
    ):
        assert _echo_is_safe(replies.word_problem(numbers))
    for topic in load_curriculum().topics:
        said = replies.think_first(topic)
        assert topic.title in said and "?" in said
        assert _echo_is_safe(said), said
