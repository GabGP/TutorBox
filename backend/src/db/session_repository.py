"""Repository functions for quiz session persistence."""

import sqlite3

from db.round_repository import (
    create_quiz_round,
    get_quiz_round,
    get_round_by_index,
    list_rounds_for_session,
    update_quiz_round_status,
)
from db.session_mapper import row_to_quiz_session
from session.models import QuizSessionRecord, SessionStatus

__all__ = [
    "create_quiz_round",
    "create_quiz_session",
    "get_quiz_round",
    "get_quiz_session",
    "get_round_by_index",
    "list_rounds_for_session",
    "update_quiz_round_status",
    "update_quiz_session_status",
]


def create_quiz_session(
    conn: sqlite3.Connection,
    session_id: str,
    title: str,
    topic: str,
    *,
    teacher_id: int | None = None,
    question_count: int = 0,
) -> QuizSessionRecord:
    """Inserts a new quiz session in lobby state and returns its record."""
    conn.execute(
        """
        INSERT INTO quiz_sessions (
            id, title, topic, teacher_id, status, question_count, current_round_index
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (
            session_id,
            title,
            topic,
            teacher_id,
            SessionStatus.LOBBY.value,
            question_count,
        ),
    )
    created_session = get_quiz_session(conn, session_id)
    if created_session is None:
        raise RuntimeError(f"Failed to retrieve newly created session '{session_id}'.")
    return created_session


def get_quiz_session(
    conn: sqlite3.Connection, session_id: str
) -> QuizSessionRecord | None:
    """Retrieves a quiz session by its unique ID."""
    cursor = conn.execute("SELECT * FROM quiz_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    return row_to_quiz_session(row) if row is not None else None


def update_quiz_session_status(
    conn: sqlite3.Connection,
    session_id: str,
    status: str,
    *,
    started_at: str | None = None,
    ended_at: str | None = None,
    current_round_index: int | None = None,
) -> bool:
    """Updates session status, round index, and optional lifecycle timestamps."""
    updates: list[str] = ["status = ?"]
    params: list[object] = [status]

    if started_at is not None:
        updates.append("started_at = ?")
        params.append(started_at)
    if ended_at is not None:
        updates.append("ended_at = ?")
        params.append(ended_at)
    if current_round_index is not None:
        updates.append("current_round_index = ?")
        params.append(current_round_index)

    params.append(session_id)
    query = f"UPDATE quiz_sessions SET {', '.join(updates)} WHERE id = ?"
    cursor = conn.execute(query, params)
    return cursor.rowcount > 0
