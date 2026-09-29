"""Mode 2 telemetry: one turn_logs row per tutor turn (docs/database/dialogue.md)."""

import sqlite3
from dataclasses import dataclass

__all__ = ["TurnRecord", "record_turn"]


@dataclass(frozen=True)
class TurnRecord:
    """A tutor turn as stored: what the child wrote and what the tutor answered."""

    session_id: str
    user_input: str
    final_response: str
    hint_level: int
    containment_triggered: bool
    expression: str | None = None
    target: str | None = None
    is_correct: bool | None = None
    llm_raw: str | None = None


def record_turn(conn: sqlite3.Connection, record: TurnRecord) -> None:
    """Inserts one turn. The caller commits."""
    conn.execute(
        "INSERT INTO turn_logs (session_id, user_input, sympy_evaluated_expression, "
        "sympy_target_result, sympy_is_correct, llm_raw_response, "
        "containment_triggered, final_response, hint_level) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            record.session_id,
            record.user_input,
            record.expression,
            record.target,
            None if record.is_correct is None else int(record.is_correct),
            record.llm_raw,
            int(record.containment_triggered),
            record.final_response,
            record.hint_level,
        ),
    )
