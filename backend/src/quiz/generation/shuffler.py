"""Utility for permuting quiz options and diagnostic distractors."""

import random

from quiz.contracts.models import (
    DistractorDetail,
    OptionKey,
    QuizQuestion,
)

ORDERED_OPTION_KEYS: list[OptionKey] = ["A", "B", "C", "D"]


def shuffle_quiz_question(
    question: QuizQuestion,
    rng: random.Random | None = None,
) -> QuizQuestion:
    """Permutes question options and distractors across keys A, B, C, D.

    Randomly distributes the correct answer and diagnostic distractors
    while strictly preserving the binding between distractor option values
    and their underlying misconception explanation details.
    """
    active_rng = rng if rng is not None else random.Random()

    correct_item: tuple[str, DistractorDetail | None] = (
        question.options[question.correct_option],
        None,
    )
    distractor_items: list[tuple[str, DistractorDetail | None]] = [
        (question.options[key], question.distractors[key])
        for key in sorted(question.distractors.keys())
    ]

    all_items = [correct_item, *distractor_items]
    active_rng.shuffle(all_items)

    new_options: dict[str, str] = {}
    new_distractors: dict[str, DistractorDetail] = {}
    new_correct_option: OptionKey = "A"

    for key, (option_text, distractor_detail) in zip(ORDERED_OPTION_KEYS, all_items):
        new_options[key] = option_text
        if distractor_detail is None:
            new_correct_option = key
        else:
            new_distractors[key] = distractor_detail

    return QuizQuestion(
        id=question.id,
        topic=question.topic,
        subconcept=question.subconcept,
        question_text=question.question_text,
        options=new_options,
        correct_option=new_correct_option,
        distractors=new_distractors,
    )
