"""Database repository for quiz generation telemetry and observability logs."""

import json
import sqlite3
from typing import Any

DEFAULT_TELEMETRY_LOG_LIMIT: int = 50


def record_generation_log(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    topic: str,
    model_name: str,
    attempts: int,
    duration_ms: float,
    success: bool,
    question_id: str | None = None,
    subconcept: str | None = None,
    rejection_history: list[str] | None = None,
) -> int:
    """Inserts a quiz generation telemetry log and returns its row ID."""
    rejection_json = (
        json.dumps(rejection_history) if rejection_history is not None else None
    )
    cursor = conn.execute(
        """
        INSERT INTO quiz_generation_logs (
            question_id, user_id, topic, subconcept, model_name,
            attempts, duration_ms, success, rejection_history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question_id,
            user_id,
            topic,
            subconcept,
            model_name,
            attempts,
            duration_ms,
            1 if success else 0,
            rejection_json,
        ),
    )
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError("Failed to obtain inserted telemetry record ID.")
    return row_id


def _row_to_telemetry_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Converts a database row into a structured telemetry dictionary."""
    rejection_json = row["rejection_history_json"]
    return {
        "id": row["id"],
        "question_id": row["question_id"],
        "user_id": row["user_id"],
        "topic": row["topic"],
        "subconcept": row["subconcept"],
        "model_name": row["model_name"],
        "attempts": row["attempts"],
        "duration_ms": float(row["duration_ms"]),
        "success": bool(row["success"]),
        "rejection_history": json.loads(rejection_json) if rejection_json else [],
        "created_at": row["created_at"],
    }


def get_generation_log_by_id(
    conn: sqlite3.Connection, log_id: int
) -> dict[str, Any] | None:
    """Retrieves a single quiz generation telemetry record by ID."""
    cursor = conn.execute("SELECT * FROM quiz_generation_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    return _row_to_telemetry_dict(row) if row is not None else None


def list_generation_logs(
    conn: sqlite3.Connection,
    *,
    user_id: int | None = None,
    topic: str | None = None,
    success: bool | None = None,
    limit: int = DEFAULT_TELEMETRY_LOG_LIMIT,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Lists generation telemetry logs with optional filtering and pagination."""
    clauses: list[str] = []
    params: list[object] = []
    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    if topic is not None:
        clauses.append("topic = ?")
        params.append(topic)
    if success is not None:
        clauses.append("success = ?")
        params.append(1 if success else 0)

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        f"SELECT * FROM quiz_generation_logs{where_sql} "
        f"ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    cursor = conn.execute(query, params)
    return [_row_to_telemetry_dict(row) for row in cursor.fetchall()]


def get_generation_summary_metrics(
    conn: sqlite3.Connection,
    *,
    topic: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Computes aggregated generation metrics (success rate, avg latency, avg attempts)."""
    clauses: list[str] = []
    params: list[object] = []
    if topic is not None:
        clauses.append("topic = ?")
        params.append(topic)
    if model_name is not None:
        clauses.append("model_name = ?")
        params.append(model_name)

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT
            COUNT(*) AS total_generations,
            COALESCE(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END), 0) AS successful_generations,
            COALESCE(AVG(attempts), 0.0) AS avg_attempts,
            COALESCE(AVG(duration_ms), 0.0) AS avg_duration_ms
        FROM quiz_generation_logs{where_sql}
    """
    cursor = conn.execute(query, params)
    row = cursor.fetchone()

    total = int(row["total_generations"]) if row else 0
    successful = int(row["successful_generations"]) if row else 0
    return {
        "total_generations": total,
        "successful_generations": successful,
        "failed_generations": total - successful,
        "success_rate": round(successful / total, 4) if total > 0 else 0.0,
        "avg_attempts": round(float(row["avg_attempts"]), 2) if row else 0.0,
        "avg_duration_ms": round(float(row["avg_duration_ms"]), 2) if row else 0.0,
    }
