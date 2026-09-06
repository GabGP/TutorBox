"""Unit tests for session route dependencies and entity resolvers."""

import pytest
from fastapi import HTTPException

from src.api.session.dependencies import get_session_and_current_round


def test_get_session_and_current_round_success(temp_db):
    """Resolves existing session and its current round."""
    _, conn = temp_db
    session_id = "s_dep_test_001"
    round_id = "r_dep_test_001"
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic, status, current_round_index, question_count) "
        "VALUES (?, ?, ?, 'active', 0, 1)",
        (session_id, "Dependency Test", "arithmetic"),
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index, status) "
        "VALUES (?, ?, 0, 'open')",
        (round_id, session_id),
    )
    conn.commit()

    session, current_round = get_session_and_current_round(conn, session_id)
    assert session.id == session_id
    assert current_round.id == round_id
    assert current_round.session_id == session_id
    assert current_round.round_index == 0


def test_get_session_and_current_round_session_not_found(temp_db):
    """Raises HTTP 404 when session does not exist."""
    _, conn = temp_db
    with pytest.raises(HTTPException) as exc_info:
        get_session_and_current_round(conn, "s_nonexistent")
    assert exc_info.value.status_code == 404
    assert "Session 's_nonexistent' not found." in exc_info.value.detail


def test_get_session_and_current_round_missing_round(temp_db):
    """Raises HTTP 404 when session references a missing round index."""
    _, conn = temp_db
    session_id = "s_orphan_round"
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic, status, current_round_index, question_count) "
        "VALUES (?, ?, ?, 'lobby', 99, 1)",
        (session_id, "Corrupted Session", "arithmetic"),
    )
    conn.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_session_and_current_round(conn, session_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Round not found."
