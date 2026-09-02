"""Settings builder, parser, and cached accessor for TutorBox."""

import os

from config.constants import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    DEFAULT_BCRYPT_ROUNDS,
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_QUIZ_MAX_RETRIES,
    DEFAULT_SIGNUP_MAX_EVENTS,
    DEFAULT_SIGNUP_WINDOW_SECONDS,
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
)
from config.models import (
    DatabaseConfig,
    LLMConfig,
    QuizConfig,
    SecurityConfig,
    Settings,
)
from config.parsers import parse_db_path, parse_float, parse_int

__all__ = ["clear_settings_cache", "get_settings"]

_settings_instance: Settings | None = None


def clear_settings_cache() -> None:
    """Clears the cached Settings instance."""
    global _settings_instance
    _settings_instance = None


def get_settings(*, reload: bool = False) -> Settings:
    """Returns the centralized typed application settings."""
    global _settings_instance
    if _settings_instance is not None and not reload:
        return _settings_instance

    _settings_instance = Settings(
        database=DatabaseConfig(
            database_path=parse_db_path(os.environ.get("DATABASE_PATH")),
            busy_timeout_ms=parse_int(
                "DB_BUSY_TIMEOUT_MS", DEFAULT_BUSY_TIMEOUT_MS, min_value=1
            ),
        ),
        security=SecurityConfig(
            bcrypt_rounds=parse_int(
                "BCRYPT_ROUNDS", DEFAULT_BCRYPT_ROUNDS, min_value=4, max_value=31
            ),
            auth_max_attempts=parse_int(
                "AUTH_MAX_ATTEMPTS", DEFAULT_AUTH_MAX_ATTEMPTS, min_value=1
            ),
            auth_lockout_seconds=parse_int(
                "AUTH_LOCKOUT_SECONDS", DEFAULT_AUTH_LOCKOUT_SECONDS, min_value=1
            ),
            auth_max_tracked_keys=parse_int(
                "AUTH_MAX_TRACKED_KEYS", DEFAULT_AUTH_MAX_TRACKED_KEYS, min_value=1
            ),
            signup_max_events=parse_int(
                "SIGNUP_RATE_LIMIT_MAX_EVENTS", DEFAULT_SIGNUP_MAX_EVENTS, min_value=1
            ),
            signup_window_seconds=parse_int(
                "SIGNUP_RATE_LIMIT_WINDOW_SECONDS",
                DEFAULT_SIGNUP_WINDOW_SECONDS,
                min_value=1,
            ),
        ),
        llm=LLMConfig(
            base_url=(os.environ.get("SLM_BASE_URL") or DEFAULT_SLM_BASE_URL).rstrip(
                "/"
            ),
            model_name=os.environ.get("SLM_MODEL_NAME") or DEFAULT_SLM_MODEL_NAME,
            temperature=parse_float(
                "SLM_TEMPERATURE",
                DEFAULT_SLM_TEMPERATURE,
                min_value=0.0,
                max_value=2.0,
            ),
            timeout_seconds=parse_float(
                "SLM_TIMEOUT_SECONDS",
                DEFAULT_SLM_TIMEOUT_SECONDS,
                min_value=0.1,
                fallback_env_name="SLM_TIMEOUT",
            ),
        ),
        quiz=QuizConfig(
            max_retries=parse_int(
                "QUIZ_MAX_RETRIES", DEFAULT_QUIZ_MAX_RETRIES, min_value=1
            ),
        ),
    )
    return _settings_instance
