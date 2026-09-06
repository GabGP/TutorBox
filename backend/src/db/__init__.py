"""TutorBox DB package."""

from . import (
    audit,
    database,
    migrations,
    question_mapper,
    question_repository,
    round_repository,
    session_mapper,
    session_repository,
    telemetry_repository,
    vote_repository,
)
from .audit import VALID_ACTIONS, record_audit
from .telemetry_repository import (
    get_generation_log_by_id,
    get_generation_summary_metrics,
    list_generation_logs,
    record_generation_log,
)

# Backward-compatibility aliases
quiz = question_repository
quiz_mapper = question_mapper
quiz_telemetry = telemetry_repository

__all__ = [
    "VALID_ACTIONS",
    "audit",
    "database",
    "get_generation_log_by_id",
    "get_generation_summary_metrics",
    "list_generation_logs",
    "migrations",
    "question_mapper",
    "question_repository",
    "quiz",
    "quiz_mapper",
    "quiz_telemetry",
    "record_audit",
    "record_generation_log",
    "round_repository",
    "session_mapper",
    "session_repository",
    "telemetry_repository",
    "vote_repository",
]
