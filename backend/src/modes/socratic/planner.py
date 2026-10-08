"""Decides the tutor's next move from the child's message and the conversation.

Deterministic and model-free: it checks the input, refuses what is outside the
CNB, judges answers with SymPy and climbs the hint ladder. A Move says what to
say (`text`) and whether the model may reword it ("rewrite") or explain a CNB
concept in its own words ("explain"); guard.py checks the model either way.
"""

from dataclasses import dataclass, replace
from fractions import Fraction

from modes.socratic import hints, replies
from modes.socratic.curriculum import Topic, load_curriculum
from modes.socratic.input_guard import check_input, clean_input
from modes.socratic.lexicon import HELP
from modes.socratic.numbers import digits_for_words, extract_numbers
from modes.socratic.problems import (
    Problem,
    accepted_answers,
    find_attempt,
    find_problem,
)
from modes.socratic.reading import bare_answer, is_question, numeric_topic
from modes.socratic.state import Conversation
from modes.socratic.text import Folded

__all__ = ["MAX_LEVEL", "Move", "plan"]

MAX_LEVEL = 3


@dataclass(frozen=True)
class Move:
    """The reply chosen for one message, and what the model may do with it."""

    kind: str
    text: str
    llm: str = "none"  # "none" | "rewrite" | "explain"
    problem: Problem | None = None
    level: int = 0
    is_correct: bool | None = None
    topic: Topic | None = None
    question: str = ""
    attempt: Fraction | None = None  # the value the child typed, when it was judged


def plan(conversation: Conversation, message: str) -> tuple[Move, Conversation]:
    """The next move, and the conversation as it stands after it."""
    if (issue := check_input(message)) is not None:
        return Move("input", replies.INPUT[issue]), conversation
    message = digits_for_words(clean_input(message))  # "doce más cinco" is 12 + 5
    folded = Folded.of(message)
    curriculum = load_curriculum()
    if curriculum.is_beyond(folded):
        return Move("beyond", replies.BEYOND), conversation
    if (attempt := find_attempt(message)) is not None:
        problem, value = attempt
        same = conversation.problem == problem
        return _judge(problem, value, conversation.level if same else 0)
    if (problem := find_problem(message)) is not None:
        return _start(problem)
    if (answer := bare_answer(message, folded)) is not None:
        return _answer(conversation, answer)
    if (text := replies.social(folded)) is not None:
        return Move("social", text), conversation
    topic = curriculum.match(folded) or numeric_topic(message, folded)
    numbers = extract_numbers(message)
    if topic is not None and len(numbers) >= 2:
        move = Move("word_problem", replies.word_problem(numbers), llm="rewrite")
        return move, Conversation(word_numbers=tuple(numbers))
    if (current := conversation.problem) is not None:
        if folded.has_any(HELP) or (topic is None and len(folded.tokens) <= 4):
            return _next_hint(current, conversation)
        if topic is None:
            return Move("off_topic", replies.back_to(current)), conversation
    if topic is None:
        answering = "?" not in message and not is_question(folded)
        if conversation.topic_id is not None and answering:
            return _idea(conversation.topic_id)
        return Move("off_topic", replies.OFF_TOPIC), conversation
    explained = replace(conversation, topic_id=topic.id)
    if folded.has_any(("cuanto*", "cuanta*")):
        move = Move("think", replies.think_first(topic), llm="rewrite", topic=topic)
        return move, explained
    fallback = replies.explain_fallback(topic)
    move = Move("explain", fallback, llm="explain", topic=topic, question=message)
    return move, explained


def _start(problem: Problem) -> tuple[Move, Conversation]:
    if problem.target < 0:
        return Move("negative", replies.NEGATIVE), Conversation()
    text = hints.hint(problem, 0)
    return Move("hint", text, llm="rewrite", problem=problem), Conversation(problem)


def _judge(problem: Problem, value: Fraction, level: int) -> tuple[Move, Conversation]:
    if problem.target < 0:
        return Move("negative", replies.NEGATIVE), Conversation()
    if value in accepted_answers(problem):
        praise = replies.praise(problem)
        move = Move("praise", praise, problem=problem, level=level, is_correct=True)
        return replace(move, attempt=value), Conversation()
    level = min(level + 1, MAX_LEVEL)
    text = f"Todavía no. {hints.hint(problem, level)}"
    move = Move(
        "hint", text, llm="rewrite", problem=problem, level=level, is_correct=False
    )
    return replace(move, attempt=value), Conversation(problem, level)


def _next_hint(
    problem: Problem, conversation: Conversation
) -> tuple[Move, Conversation]:
    level = min(conversation.level + 1, MAX_LEVEL)
    text = hints.hint(problem, level)
    move = Move("hint", text, llm="rewrite", problem=problem, level=level)
    return move, replace(conversation, level=level)


def _answer(conversation: Conversation, value: Fraction) -> tuple[Move, Conversation]:
    if conversation.problem is not None:
        return _judge(conversation.problem, value, conversation.level)
    if conversation.word_numbers:
        return Move("show_work", replies.SHOW_WORK), conversation
    if conversation.topic_id is not None:
        return _idea(conversation.topic_id)
    return Move("orphan", replies.ORPHAN_ANSWER), conversation


def _idea(topic_id: str) -> tuple[Move, Conversation]:
    """The child answers the tutor's '¿Me das un ejemplo tuyo?' after an explanation."""
    topic = load_curriculum().get(topic_id)
    return Move("idea", replies.idea_thanks(topic), topic=topic), Conversation()
