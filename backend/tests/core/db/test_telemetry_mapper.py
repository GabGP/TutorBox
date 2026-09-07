"""Unit tests for quiz generation telemetry row mapper."""

import sqlite3

from core.db.telemetry_mapper import row_to_telemetry_dict


def test_row_to_telemetry_dict_with_rejections() -> None:
    """Verifies row mapping when rejection history JSON is populated."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            1 AS id,
            'q1' AS question_id,
            42 AS user_id,
            'fractions' AS topic,
            'addition' AS subconcept,
            'qwen' AS model_name,
            2 AS attempts,
            '123.45' AS duration_ms,
            1 AS success,
            '["error 1", "error 2"]' AS rejection_history_json,
            '2026-09-07T00:00:00' AS created_at
        """
    )
    row = cursor.fetchone()
    assert row is not None

    telemetry = row_to_telemetry_dict(row)
    assert telemetry["id"] == 1
    assert telemetry["question_id"] == "q1"
    assert telemetry["user_id"] == 42
    assert telemetry["topic"] == "fractions"
    assert telemetry["subconcept"] == "addition"
    assert telemetry["model_name"] == "qwen"
    assert telemetry["attempts"] == 2
    assert telemetry["duration_ms"] == 123.45
    assert telemetry["success"] is True
    assert telemetry["rejection_history"] == ["error 1", "error 2"]
    assert telemetry["created_at"] == "2026-09-07T00:00:00"
    conn.close()


def test_row_to_telemetry_dict_null_rejections() -> None:
    """Verifies row mapping when rejection history JSON is null."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            2 AS id,
            NULL AS question_id,
            10 AS user_id,
            'arithmetic' AS topic,
            NULL AS subconcept,
            'mock' AS model_name,
            1 AS attempts,
            50.0 AS duration_ms,
            0 AS success,
            NULL AS rejection_history_json,
            '2026-09-07T00:00:00' AS created_at
        """
    )
    row = cursor.fetchone()
    assert row is not None

    telemetry = row_to_telemetry_dict(row)
    assert telemetry["id"] == 2
    assert telemetry["question_id"] is None
    assert telemetry["subconcept"] is None
    assert telemetry["success"] is False
    assert telemetry["rejection_history"] == []
    conn.close()
