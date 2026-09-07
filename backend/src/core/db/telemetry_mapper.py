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
