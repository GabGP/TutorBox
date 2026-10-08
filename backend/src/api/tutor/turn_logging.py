"""Turn logging for Mode 2: one turn_logs row per tutor turn, with its labels.

The labels come from modes/socratic/telemetry/ and describe the turn the engine has
already decided. Building a row never changes the reply the child receives.
"""

from core.db.database import get_db
from core.db.turn_log_repository import TurnRecord, record_turn
from modes.socratic import TurnResult
from modes.socratic.telemetry import classify_error, concept_for, scaffolding_strategy

__all__ = ["build_turn_record", "log_turn"]


def build_turn_record(session_id: str, message: str, result: TurnResult) -> TurnRecord:
    """The turn_logs row for one tutor turn, labels included. Touches no database."""
    problem = result.problem
    concept = concept_for(problem, result.topic_id)
    return TurnRecord(
        session_id=session_id,
        user_input=message,
        final_response=result.reply,
        hint_level=result.hint_level,
        containment_triggered=result.containment_triggered,
        expression=problem.text if problem else None,
        target=str(problem.target) if problem else None,
        is_correct=result.is_correct,
        llm_raw=result.llm_raw,
        concept_topic=concept.topic,
        concept_subconcept=concept.subconcept,
        cnb_topic=concept.cnb_topic,
        error_type=_wrong_answer_error_type(result),
        scaffolding_strategy=scaffolding_strategy(result.kind, result.hint_level),
    )


def log_turn(session_id: str, message: str, result: TurnResult) -> None:
    """Stores the turn's row in turn_logs and commits it."""
    record = build_turn_record(session_id, message, result)
    with get_db() as conn:
        record_turn(conn, record)
        conn.commit()


def _wrong_answer_error_type(result: TurnResult) -> str | None:
    """The misconception behind a judged wrong answer; None for every other turn."""
    problem, attempt = result.problem, result.attempt
    if result.is_correct is False and problem is not None and attempt is not None:
        return classify_error(problem, attempt)
    return None
