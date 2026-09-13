"""Spoken script for the >51% intervention.

The rule itself lives in `evaluator.py`: when a single diagnostic distractor takes more than
51% of the votes, the class shares one misconception and the appliance says so out loud. This
module turns that decision into the sentences the teacher's device reads, in classroom Spanish.
"""

from modes.quiz.session.models import RoundTally, TurnDecision

__all__ = ["build_intervention_script"]


def build_intervention_script(
    options: dict[str, str],
    tally: RoundTally,
    decision: TurnDecision,
) -> str:
    """Composes what the appliance says when one wrong answer takes more than 51% of the class.

    Raises ValueError when the round did not trigger the rule: the classroom stays silent
    unless the evaluator says otherwise.
    """
    if not decision.should_speak or decision.dominant_distractor is None:
        raise ValueError(
            f"Round did not trigger the >51% rule (reason: {decision.reason})."
        )

    chosen_text = options.get(
        decision.dominant_distractor, decision.dominant_distractor
    )
    correct_text = options.get(tally.correct_option, tally.correct_option)
    share = round(decision.dominant_percentage)

    sentences = [
        f"Atención: {share} por ciento del grupo respondió {chosen_text}.",
        (decision.explanation or "").strip(),
        f"La respuesta correcta es {correct_text}.",
    ]
    return " ".join(sentence for sentence in sentences if sentence)
