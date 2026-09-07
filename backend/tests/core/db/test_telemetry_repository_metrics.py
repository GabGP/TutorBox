"""Aggregation and metrics reporting tests for quiz generation telemetry repository."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from core.db.telemetry_repository import (
    get_generation_summary_metrics,
    record_generation_log,
)


def _create_dummy_user(conn: sqlite3.Connection, username: str = "teacher1") -> int:
    """Helper to insert a user and return its ID."""
    cursor = conn.execute(
        "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
        (username, "hash123", "teacher"),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


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


def test_record_generation_log_none_lastrowid_raises() -> None:
    """Verifies that an unexpected None lastrowid raises RuntimeError."""
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
