"""Unit and property tests for the quiz option and misconception shuffler."""

import random

from quiz.contracts.models import DistractorDetail, QuizQuestion
from quiz.generation.shuffler import shuffle_quiz_question


def create_sample_question(correct_option: str = "A") -> QuizQuestion:
    """Helper to build a valid sample QuizQuestion."""
    options = {"A": "11", "B": "14", "C": "10", "D": "24"}
    distractor_data = {
        "A": ("forgot_carry", "Olvidaste llevar la decena."),
        "B": ("left_to_right_precedence", "Sumaste antes de multiplicar."),
        "C": ("multiplication_error", "Multiplicaste mal."),
        "D": ("multiplied_all", "Multiplicaste todos los factores."),
    }

    distractors: dict[str, DistractorDetail] = {}
    for key, (misconception, explanation) in distractor_data.items():
        if key != correct_option:
            distractors[key] = DistractorDetail(
                misconception=misconception,
                explanation=explanation,
            )

    return QuizQuestion(
        id="q_shuffle_test_01",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 3 + 4 * 2?",
        options=options,
        correct_option=correct_option,
        distractors=distractors,
    )


def test_shuffler_preserves_correct_answer_value():
    question = create_sample_question(correct_option="A")
    original_correct_value = question.options[question.correct_option]

    for seed in range(20):
        rng = random.Random(seed)
        shuffled = shuffle_quiz_question(question, rng=rng)

        assert shuffled.id == question.id
        assert shuffled.topic == question.topic
        assert shuffled.subconcept == question.subconcept
        assert shuffled.question_text == question.question_text
        assert shuffled.options[shuffled.correct_option] == original_correct_value


def test_shuffler_preserves_distractor_bindings():
    question = create_sample_question(correct_option="A")
    expected_bindings = {
        question.options[key]: (
            question.distractors[key].misconception,
            question.distractors[key].explanation,
        )
        for key in question.distractors
    }

    for seed in range(30):
        rng = random.Random(seed)
        shuffled = shuffle_quiz_question(question, rng=rng)

        assert len(shuffled.distractors) == 3
        for dist_key, dist_detail in shuffled.distractors.items():
            dist_option_val = shuffled.options[dist_key]
            expected_misconception, expected_explanation = expected_bindings[
                dist_option_val
            ]
            assert dist_detail.misconception == expected_misconception
            assert dist_detail.explanation == expected_explanation


def test_shuffler_uniform_distribution_of_correct_option():
    question = create_sample_question(correct_option="A")
    counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    total_runs = 200

    for seed in range(total_runs):
        rng = random.Random(seed * 7 + 13)
        shuffled = shuffle_quiz_question(question, rng=rng)
        counts[shuffled.correct_option] += 1

    # Over 200 runs, each key expected ~50 times. All keys should receive >= 20.
    for key in ["A", "B", "C", "D"]:
        assert counts[key] >= 20, (
            f"Key {key} underrepresented in shuffling: {counts[key]}"
        )


def test_shuffler_misconception_ordering_is_permuted():
    question = create_sample_question(correct_option="A")
    distinct_misconception_permutations: set[tuple[str, ...]] = set()

    for seed in range(50):
        rng = random.Random(seed)
        shuffled = shuffle_quiz_question(question, rng=rng)
        ordered_misconceptions = tuple(
            shuffled.distractors[k].misconception
            for k in sorted(shuffled.distractors.keys())
        )
        distinct_misconception_permutations.add(ordered_misconceptions)

    # Distractors should appear in multiple varied permutations
    assert len(distinct_misconception_permutations) > 5


def test_shuffler_deterministic_with_fixed_seed():
    question = create_sample_question(correct_option="A")
    shuffled_a = shuffle_quiz_question(question, rng=random.Random(42))
    shuffled_b = shuffle_quiz_question(question, rng=random.Random(42))

    assert shuffled_a.correct_option == shuffled_b.correct_option
    assert shuffled_a.options == shuffled_b.options
    assert shuffled_a.distractors == shuffled_b.distractors


def test_shuffler_handles_different_starting_correct_options():
    for initial_correct in ["A", "B", "C", "D"]:
        question = create_sample_question(correct_option=initial_correct)
        original_correct_value = question.options[initial_correct]

        shuffled = shuffle_quiz_question(question, rng=random.Random(100))
        assert shuffled.options[shuffled.correct_option] == original_correct_value
        assert len(shuffled.distractors) == 3


def test_shuffler_defaults_to_unseeded_random():
    question = create_sample_question(correct_option="A")
    shuffled = shuffle_quiz_question(question)
    assert shuffled.correct_option in {"A", "B", "C", "D"}
    assert len(shuffled.options) == 4
    assert len(shuffled.distractors) == 3
