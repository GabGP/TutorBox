"""Row mappers for quiz generation telemetry records."""

import json
import sqlite3
from typing import Any


def row_to_telemetry_dict(row: sqlite3.Row) -> dict[str, Any]:
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


def build_telemetry_filter_clauses(
    *,
    user_id: int | None = None,
    topic: str | None = None,
    success: bool | None = None,
) -> tuple[str, list[object]]:
    """Builds WHERE SQL and params for user/topic/success log filters."""
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
    return where_sql, params
