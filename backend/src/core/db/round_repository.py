"""Repository functions for quiz question round persistence."""

import sqlite3

from core.db.session_mapper import row_to_quiz_round
from session.models import QuizRoundRecord


def create_quiz_round(
    conn: sqlite3.Connection,
    round_id: str,
    session_id: str,
    round_index: int,
    *,
    question_id: str | None = None,
    duration_seconds: int = 30,
) -> QuizRoundRecord:
    """Inserts a question round for a session and returns its record."""
    conn.execute(
        """
        INSERT INTO quiz_session_rounds (
            id, session_id, question_id, round_index, duration_seconds
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (round_id, session_id, question_id, round_index, duration_seconds),
    )
    round_record = get_quiz_round(conn, round_id)
    if round_record is None:
        raise RuntimeError(f"Failed to retrieve created round '{round_id}'.")
    return round_record


def get_quiz_round(conn: sqlite3.Connection, round_id: str) -> QuizRoundRecord | None:
    """Retrieves an individual round by its unique ID."""
    cursor = conn.execute("SELECT * FROM quiz_session_rounds WHERE id = ?", (round_id,))
    row = cursor.fetchone()
    return row_to_quiz_round(row) if row is not None else None


def get_round_by_index(
    conn: sqlite3.Connection, session_id: str, round_index: int
) -> QuizRoundRecord | None:
    """Retrieves a round by session ID and 0-based round index."""
    cursor = conn.execute(
        "SELECT * FROM quiz_session_rounds WHERE session_id = ? AND round_index = ?",
        (session_id, round_index),
    )
    row = cursor.fetchone()
    return row_to_quiz_round(row) if row is not None else None


def update_quiz_round_status(
    conn: sqlite3.Connection,
    round_id: str,
    status: str,
    *,
    opened_at: str | None = None,
    closed_at: str | None = None,
) -> bool:
    """Updates round status and optional opened/closed timestamps."""
    updates: list[str] = ["status = ?"]
    params: list[object] = [status]

    if opened_at is not None:
        updates.append("opened_at = ?")
        params.append(opened_at)
    if closed_at is not None:
        updates.append("closed_at = ?")
        params.append(closed_at)

    params.append(round_id)
    query = f"UPDATE quiz_session_rounds SET {', '.join(updates)} WHERE id = ?"
    cursor = conn.execute(query, params)
    return cursor.rowcount > 0


def list_rounds_for_session(
    conn: sqlite3.Connection, session_id: str
) -> list[QuizRoundRecord]:
    """Returns all rounds for a given session sorted by round index."""
    cursor = conn.execute(
        "SELECT * FROM quiz_session_rounds WHERE session_id = ? ORDER BY round_index ASC",
        (session_id,),
    )
    return [row_to_quiz_round(row) for row in cursor.fetchall()]
