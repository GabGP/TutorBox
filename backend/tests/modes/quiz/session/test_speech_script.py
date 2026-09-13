"""Unit tests for the spoken >51% intervention script (src/modes/quiz/session/speech.py)."""

import pytest

from modes.quiz.session.aggregator import compute_tally_from_counts
from modes.quiz.session.evaluator import evaluate_turn_decision
from modes.quiz.session.models import TurnDecision
from modes.quiz.session.speech import build_intervention_script

OPTIONS = {"A": "3/4", "B": "1/2", "C": "2/3", "D": "5/8"}
DISTRACTORS = {
    "B": {
        "misconception": "halved_numerator_only",
        "explanation": "Dividiste sólo el numerador entre 2 y dejaste el denominador igual.",
    },
    "C": {
        "misconception": "wrong_factor",
        "explanation": "Usaste el factor equivocado.",
    },
    "D": {
        "misconception": "kept_denominator",
        "explanation": "Conservaste el denominador.",
    },
}


def _decision(counts: dict[str, int]):
    tally = compute_tally_from_counts(counts, correct_option="A")
    return tally, evaluate_turn_decision(tally, DISTRACTORS)


def test_script_names_the_share_the_mistake_and_the_right_answer() -> None:
    """Verifies the spoken script frames the class share, the why, and the correct answer."""
    tally, decision = _decision({"A": 4, "B": 16, "C": 0, "D": 0})

    script = build_intervention_script(OPTIONS, tally, decision)

    assert script.startswith("Atención: 80 por ciento del grupo respondió 1/2.")
    assert "Dividiste sólo el numerador" in script
    assert script.endswith("La respuesta correcta es 3/4.")


def test_script_survives_a_question_without_distractor_metadata() -> None:
    """Verifies a missing explanation still yields a usable classroom sentence."""
    tally, _ = _decision({"A": 1, "B": 9, "C": 0, "D": 0})
    decision = TurnDecision(
        should_speak=True,
        reason="dominant_distractor_exceeded_threshold",
        dominant_distractor="B",
        dominant_percentage=90.0,
        misconception=None,
        explanation=None,
    )

    script = build_intervention_script(OPTIONS, tally, decision)

    assert script == (
        "Atención: 90 por ciento del grupo respondió 1/2. La respuesta correcta es 3/4."
    )


def test_script_refuses_to_speak_when_the_rule_did_not_trigger() -> None:
    """Verifies scattered or mostly-correct rounds cannot produce audio."""
    _, silent_decision = _decision({"A": 6, "B": 2, "C": 1, "D": 1})
    tally, _ = _decision({"A": 6, "B": 2, "C": 1, "D": 1})

    with pytest.raises(ValueError, match="did not trigger"):
        build_intervention_script(OPTIONS, tally, silent_decision)
