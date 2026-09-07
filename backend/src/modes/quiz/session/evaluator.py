"""Deterministic >51% Rule evaluator for spoken pedagogical intervention."""

from typing import Any

from modes.quiz.session.aggregator import find_top_distractor
from modes.quiz.session.models import RoundTally, TurnDecision

STRICT_THRESHOLD_RATIO: float = 0.51


def _extract_distractor_metadata(
    distractor_payload: Any,
) -> tuple[str | None, str | None]:
    """Safely extracts misconception slug and explanation text from distractor metadata."""
    if distractor_payload is None:
        return None, None
    if hasattr(distractor_payload, "misconception") and hasattr(
        distractor_payload, "explanation"
    ):
        return distractor_payload.misconception, distractor_payload.explanation
    if isinstance(distractor_payload, dict):
        return (
            distractor_payload.get("misconception"),
            distractor_payload.get("explanation"),
        )
    return None, None


def evaluate_turn_decision(
    tally: RoundTally,
    distractors: dict[str, Any] | None = None,
) -> TurnDecision:
    """Evaluates whether to trigger spoken remediation based on the >51% Rule.

    Spoken remediation triggers strictly when a single diagnostic distractor
    captures > 51.0% of total submitted votes.
    """
    if tally.total_votes == 0:
        return TurnDecision(
            should_speak=False,
            reason="no_votes",
            dominant_distractor=None,
            dominant_percentage=0.0,
            misconception=None,
            explanation=None,
        )

    correct_ratio = tally.correct_count / tally.total_votes
    if correct_ratio > STRICT_THRESHOLD_RATIO:
        return TurnDecision(
            should_speak=False,
            reason="majority_correct",
            dominant_distractor=None,
            dominant_percentage=round(correct_ratio * 100, 2),
            misconception=None,
            explanation=None,
        )

    top_distractor, top_count, has_tie = find_top_distractor(tally)

    if has_tie:
        tie_percentage = round((top_count / tally.total_votes) * 100, 2)
        return TurnDecision(
            should_speak=False,
            reason="tie_between_distractors",
            dominant_distractor=None,
            dominant_percentage=tie_percentage,
            misconception=None,
            explanation=None,
        )

    if top_distractor is None or top_count == 0:
        return TurnDecision(
            should_speak=False,
            reason="threshold_not_reached",
            dominant_distractor=None,
            dominant_percentage=0.0,
            misconception=None,
            explanation=None,
        )

    top_ratio = top_count / tally.total_votes
    top_percentage = round(top_ratio * 100, 2)

    if top_ratio > STRICT_THRESHOLD_RATIO:
        distractor_payload = distractors.get(top_distractor) if distractors else None
        misconception, explanation = _extract_distractor_metadata(distractor_payload)
        return TurnDecision(
            should_speak=True,
            reason="dominant_distractor_exceeded_threshold",
            dominant_distractor=top_distractor,
            dominant_percentage=top_percentage,
            misconception=misconception,
            explanation=explanation,
        )

    return TurnDecision(
        should_speak=False,
        reason="threshold_not_reached",
        dominant_distractor=top_distractor,
        dominant_percentage=top_percentage,
        misconception=None,
        explanation=None,
    )
