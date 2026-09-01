"""Unit and integration tests for quiz generation telemetry repository."""

import sqlite3

from db.quiz import create_question
from db.quiz_telemetry import (
    get_generation_log_by_id,
    get_generation_summary_metrics,
    list_generation_logs,
    record_generation_log,
)
from quiz.contracts.models import DistractorDetail, QuizQuestionCreate


def _create_dummy_user(conn: sqlite3.Connection, username: str = "teacher1") -> int:
    """Helper to insert a user and return its ID."""
    cursor = conn.execute(
        "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
        (username, "hash123", "teacher"),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def _create_sample_question(conn: sqlite3.Connection) -> str:
    """Helper to create a sample question in quiz_questions."""
    question = QuizQuestionCreate(
        topic="fractions",
        subconcept="addition",
        question_text="¿Cuánto es 1/4 + 2/4?",
        options={"A": "3/4", "B": "3/8", "C": "2/4", "D": "1/2"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores.",
            ),
            "C": DistractorDetail(
                misconception="ignored_first_term",
                explanation="Ignoraste el primer término.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead",
                explanation="Restaste en vez de sumar.",
            ),
        },
    )
    return create_question(conn, question, source="llm", sympy_verified=True)


def test_record_and_get_success_log(temp_db: tuple[str, sqlite3.Connection]) -> None:
    """Verifies persisting and retrieving a successful quiz generation telemetry log."""
    _, conn = temp_db
    user_id = _create_dummy_user(conn, "teacher_succ")
    question_id = _create_sample_question(conn)

    log_id = record_generation_log(
        conn,
        user_id=user_id,
        topic="fractions",
        subconcept="addition",
        model_name="qwen2.5-coder-1.5b",
        attempts=1,
        duration_ms=450.5,
        success=True,
        question_id=question_id,
        rejection_history=None,
    )
    assert log_id > 0

    log = get_generation_log_by_id(conn, log_id)
    assert log is not None
    assert log["id"] == log_id
    assert log["question_id"] == question_id
    assert log["user_id"] == user_id
    assert log["topic"] == "fractions"
    assert log["subconcept"] == "addition"
    assert log["model_name"] == "qwen2.5-coder-1.5b"
    assert log["attempts"] == 1
    assert log["duration_ms"] == 450.5
    assert log["success"] is True
    assert log["rejection_history"] == []
    assert log["created_at"] is not None


def test_record_and_get_failure_log_with_rejections(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
    """Verifies persisting and retrieving a failed generation attempt with rejection trail."""
    _, conn = temp_db
    user_id = _create_dummy_user(conn, "teacher_fail")
    errors = ["Stage 1 Schema: Missing key", "Stage 3 SymPy: Solution mismatch"]

    log_id = record_generation_log(
        conn,
        user_id=user_id,
        topic="pre_algebra",
        subconcept="linear_equations",
        model_name="qwen2.5-coder-1.5b",
        attempts=3,
        duration_ms=1820.0,
        success=False,
        question_id=None,
        rejection_history=errors,
    )

    log = get_generation_log_by_id(conn, log_id)
    assert log is not None
    assert log["question_id"] is None
    assert log["success"] is False
    assert log["attempts"] == 3
    assert log["duration_ms"] == 1820.0
    assert log["rejection_history"] == errors


def test_get_nonexistent_log_returns_none(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
    """Verifies fetching an unknown log ID returns None."""
    _, conn = temp_db
    assert get_generation_log_by_id(conn, 999999) is None


def test_list_generation_logs_with_filtering(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
    """Verifies listing logs filtered by user, topic, success, and pagination."""
    _, conn = temp_db
    user_1 = _create_dummy_user(conn, "user_alpha")
    user_2 = _create_dummy_user(conn, "user_beta")

    record_generation_log(
        conn,
        user_id=user_1,
        topic="arithmetic",
        model_name="m1",
        attempts=1,
        duration_ms=200.0,
        success=True,
    )
    record_generation_log(
        conn,
        user_id=user_1,
        topic="fractions",
        model_name="m1",
        attempts=2,
        duration_ms=500.0,
        success=False,
    )
    record_generation_log(
        conn,
        user_id=user_2,
        topic="fractions",
        model_name="m1",
        attempts=1,
        duration_ms=300.0,
        success=True,
    )

    # Filter by user
    user_1_logs = list_generation_logs(conn, user_id=user_1)
    assert len(user_1_logs) == 2

    # Filter by topic
    fractions_logs = list_generation_logs(conn, topic="fractions")
    assert len(fractions_logs) == 2

    # Filter by success
    success_logs = list_generation_logs(conn, success=True)
    assert len(success_logs) == 2

    failed_logs = list_generation_logs(conn, success=False)
    assert len(failed_logs) == 1

    # Pagination limit and offset
    page_1 = list_generation_logs(conn, limit=1, offset=0)
    assert len(page_1) == 1
    page_2 = list_generation_logs(conn, limit=1, offset=1)
    assert len(page_2) == 1
    assert page_1[0]["id"] != page_2[0]["id"]


def test_get_generation_summary_metrics(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
    """Verifies aggregation of total generations, success rate, and average latency."""
    _, conn = temp_db
    # Empty DB summary
    empty_metrics = get_generation_summary_metrics(conn)
    assert empty_metrics["total_generations"] == 0
    assert empty_metrics["success_rate"] == 0.0
    assert empty_metrics["avg_attempts"] == 0.0

    user_id = _create_dummy_user(conn, "metrics_user")
    record_generation_log(
        conn,
        user_id=user_id,
        topic="percentages",
        model_name="model_a",
        attempts=1,
        duration_ms=100.0,
        success=True,
    )
    record_generation_log(
        conn,
        user_id=user_id,
        topic="percentages",
        model_name="model_a",
        attempts=3,
        duration_ms=300.0,
        success=False,
    )
    record_generation_log(
        conn,
        user_id=user_id,
        topic="arithmetic",
        model_name="model_b",
        attempts=2,
        duration_ms=400.0,
        success=True,
    )

    # Overall metrics
    overall = get_generation_summary_metrics(conn)
    assert overall["total_generations"] == 3
    assert overall["successful_generations"] == 2
    assert overall["failed_generations"] == 1
    assert overall["success_rate"] == 0.6667
    assert overall["avg_attempts"] == 2.0
    assert overall["avg_duration_ms"] == 266.67

    # Filtered by topic
    topic_metrics = get_generation_summary_metrics(conn, topic="percentages")
    assert topic_metrics["total_generations"] == 2
    assert topic_metrics["successful_generations"] == 1
    assert topic_metrics["success_rate"] == 0.5
    assert topic_metrics["avg_attempts"] == 2.0
    assert topic_metrics["avg_duration_ms"] == 200.0

    # Filtered by model
    model_metrics = get_generation_summary_metrics(conn, model_name="model_b")
    assert model_metrics["total_generations"] == 1
    assert model_metrics["successful_generations"] == 1
    assert model_metrics["success_rate"] == 1.0


def test_question_foreign_key_on_delete_set_null(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
    """Verifies that deleting a referenced quiz question sets question_id to NULL."""
    _, conn = temp_db
    user_id = _create_dummy_user(conn, "fk_user")
    question_id = _create_sample_question(conn)

    log_id = record_generation_log(
        conn,
        user_id=user_id,
        topic="fractions",
        model_name="test_model",
        attempts=1,
        duration_ms=150.0,
        success=True,
        question_id=question_id,
    )

    # Delete question row directly
    conn.execute("DELETE FROM quiz_questions WHERE id = ?", (question_id,))

    log = get_generation_log_by_id(conn, log_id)
    assert log is not None
    assert log["question_id"] is None


def test_record_generation_log_none_lastrowid_raises() -> None:
    """Verifies that an unexpected None lastrowid raises RuntimeError."""
    from unittest.mock import MagicMock

    import pytest

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = None
    mock_conn.execute.return_value = mock_cursor

    with pytest.raises(
        RuntimeError, match="Failed to obtain inserted telemetry record ID"
    ):
        record_generation_log(
            mock_conn,
            user_id=1,
            topic="arithmetic",
            model_name="model",
            attempts=1,
            duration_ms=10.0,
            success=True,
        )
