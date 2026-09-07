"""Formal validation and edge-case testing of the deterministic >51% Rule."""

from modes.quiz.contracts.models import DistractorDetail
from modes.quiz.session.aggregator import compute_tally_from_counts
from modes.quiz.session.evaluator import evaluate_turn_decision

MOCK_DISTRACTORS = {
    "B": DistractorDetail(
        misconception="added_instead_of_multiplied",
        explanation="Sumaste en lugar de multiplicar. Recuerda que 3 por 4 significa tres veces cuatro.",
    ),
    "C": {
        "misconception": "forgot_to_carry",
        "explanation": "Olvidaste llevar la decena al sumar la siguiente columna.",
    },
    "D": DistractorDetail(
        misconception="inverted_subtraction_order",
        explanation="Restaste el número menor del mayor en lugar de pedir prestado.",
    ),
}


def test_evaluator_zero_votes_is_silent():
    tally = compute_tally_from_counts({}, correct_option="A")
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "no_votes"
    assert decision.dominant_distractor is None
    assert decision.dominant_percentage == 0.0


def test_evaluator_majority_correct_is_silent():
    tally = compute_tally_from_counts(
        {"A": 52, "B": 24, "C": 14, "D": 10}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "majority_correct"
    assert decision.dominant_percentage == 52.0
    assert decision.dominant_distractor is None


def test_evaluator_unanimous_correct_is_silent():
    tally = compute_tally_from_counts({"A": 30}, correct_option="A")
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "majority_correct"
    assert decision.dominant_percentage == 100.0


def test_evaluator_exact_51_percent_distractor_is_silent():
    # Strict inequality test: 51 / 100 = 0.5100, which is NOT > 0.51
    tally = compute_tally_from_counts(
        {"A": 49, "B": 51, "C": 0, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "threshold_not_reached"
    assert decision.dominant_distractor == "B"
    assert decision.dominant_percentage == 51.0


def test_evaluator_strictly_greater_than_51_percent_triggers_speech():
    # 52 / 100 = 0.5200, which is > 0.51
    tally = compute_tally_from_counts(
        {"A": 48, "B": 52, "C": 0, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is True
    assert decision.reason == "dominant_distractor_exceeded_threshold"
    assert decision.dominant_distractor == "B"
    assert decision.dominant_percentage == 52.0
    assert decision.misconception == "added_instead_of_multiplied"
    assert "Sumaste en lugar de multiplicar" in (decision.explanation or "")


def test_evaluator_exact_51_percent_correct_is_silent():
    # Correct has 51 / 100 = 0.51 (not > 0.51), distractor has 49 (not > 0.51)
    tally = compute_tally_from_counts(
        {"A": 51, "B": 49, "C": 0, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "threshold_not_reached"
    assert decision.dominant_distractor == "B"


def test_evaluator_50_50_tie_between_distractors_is_silent():
    tally = compute_tally_from_counts(
        {"A": 0, "B": 50, "C": 50, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "tie_between_distractors"
    assert decision.dominant_distractor is None
    assert decision.dominant_percentage == 50.0


def test_evaluator_dispersed_distractor_votes_is_silent():
    tally = compute_tally_from_counts(
        {"A": 15, "B": 35, "C": 30, "D": 20}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is False
    assert decision.reason == "threshold_not_reached"
    assert decision.dominant_distractor == "B"
    assert decision.dominant_percentage == 35.0


def test_evaluator_unanimous_distractor_triggers_speech():
    tally = compute_tally_from_counts(
        {"A": 0, "B": 0, "C": 25, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)

    assert decision.should_speak is True
    assert decision.reason == "dominant_distractor_exceeded_threshold"
    assert decision.dominant_distractor == "C"
    assert decision.dominant_percentage == 100.0
    assert decision.misconception == "forgot_to_carry"


def test_evaluator_extracts_metadata_from_dict_and_fallback():
    # Test with dict-based distractor metadata
    tally = compute_tally_from_counts(
        {"A": 10, "B": 0, "C": 90, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)
    assert decision.should_speak is True
    assert decision.misconception == "forgot_to_carry"

    # Test when distractor metadata is None
    decision_none = evaluate_turn_decision(tally, distractors=None)
    assert decision_none.should_speak is True
    assert decision_none.misconception is None
    assert decision_none.explanation is None


def test_evaluator_small_cohort_edge_cases():
    # 1 vote: distractor B gets 1/1 = 100%
    single_vote_tally = compute_tally_from_counts(
        {"A": 0, "B": 1, "C": 0, "D": 0}, correct_option="A"
    )
    decision_single = evaluate_turn_decision(single_vote_tally, MOCK_DISTRACTORS)
    assert decision_single.should_speak is True

    # 2 votes: 1 correct, 1 distractor (50% each -> silent)
    two_votes_split = compute_tally_from_counts(
        {"A": 1, "B": 1, "C": 0, "D": 0}, correct_option="A"
    )
    decision_split = evaluate_turn_decision(two_votes_split, MOCK_DISTRACTORS)
    assert decision_split.should_speak is False
    assert decision_split.reason == "threshold_not_reached"

    # 3 votes: 2 on distractor B (66.67% -> speaks)
    three_votes = compute_tally_from_counts(
        {"A": 1, "B": 2, "C": 0, "D": 0}, correct_option="A"
    )
    decision_three = evaluate_turn_decision(three_votes, MOCK_DISTRACTORS)
    assert decision_three.should_speak is True
    assert decision_three.dominant_distractor == "B"


def test_evaluator_unsupported_distractor_metadata_type():
    tally = compute_tally_from_counts(
        {"A": 10, "B": 90, "C": 0, "D": 0}, correct_option="A"
    )
    decision = evaluate_turn_decision(tally, {"B": 42})
    assert decision.should_speak is True
    assert decision.misconception is None
    assert decision.explanation is None


def test_evaluator_zero_distractor_votes_and_minority_correct():
    from modes.quiz.session.models import RoundTally

    tally = RoundTally(
        counts={"A": 2, "B": 0, "C": 0, "D": 0},
        total_votes=10,
        percentages={"A": 20.0, "B": 0.0, "C": 0.0, "D": 0.0},
        correct_option="A",
        correct_count=2,
        correct_percentage=20.0,
    )
    decision = evaluate_turn_decision(tally, MOCK_DISTRACTORS)
    assert decision.should_speak is False
    assert decision.reason == "threshold_not_reached"
    assert decision.dominant_distractor is None
