"""CRUD and query filtering tests for quiz generation telemetry repository."""

import sqlite3

from core.db.question_repository import create_question
from core.db.telemetry_repository import (
    get_generation_log_by_id,
    list_generation_logs,
    record_generation_log,
)
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate


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
    detail = DistractorDetail(
        misconception="wrong_math", explanation="A valid explanation."
    )
    question = QuizQuestionCreate(
        topic="fractions",
        subconcept="addition",
        question_text="¿Cuánto es 1/4 + 2/4?",
        options={"A": "3/4", "B": "3/8", "C": "2/4", "D": "1/2"},
        correct_option="A",
        distractors={"B": detail, "C": detail, "D": detail},
    )
    return create_question(conn, question, source="llm", sympy_verified=True)


def test_record_and_get_success_log(
    temp_db: tuple[str, sqlite3.Connection],
) -> None:
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
