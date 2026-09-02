"""Settings builder, parser, and cached accessor for TutorBox."""

import os

from config.constants import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    DEFAULT_BCRYPT_ROUNDS,
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_DB_PATH,
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

__all__ = ["clear_settings_cache", "get_settings"]


def _parse_int(
    env_var_name: str,
    default_value: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    raw_value = os.environ.get(env_var_name)
    if raw_value is None:
        return default_value
    try:
        parsed = int(raw_value)
        if min_value is not None and parsed < min_value:
            return default_value
        if max_value is not None and parsed > max_value:
            return default_value
        return parsed
    except ValueError:
        return default_value


def _parse_float(
    env_var_name: str,
    default_value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    fallback_env_name: str | None = None,
) -> float:
    raw_value = os.environ.get(env_var_name)
    if raw_value is None and fallback_env_name is not None:
        raw_value = os.environ.get(fallback_env_name)
    if raw_value is None:
        return default_value
    try:
        parsed = float(raw_value)
        if min_value is not None and parsed < min_value:
            return default_value
        if max_value is not None and parsed > max_value:
            return default_value
        return parsed
    except ValueError:
        return default_value


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
            database_path=os.environ.get("DATABASE_PATH") or DEFAULT_DB_PATH,
            busy_timeout_ms=_parse_int(
                "DB_BUSY_TIMEOUT_MS", DEFAULT_BUSY_TIMEOUT_MS, min_value=1
            ),
        ),
        security=SecurityConfig(
            bcrypt_rounds=_parse_int(
                "BCRYPT_ROUNDS", DEFAULT_BCRYPT_ROUNDS, min_value=4, max_value=31
            ),
            auth_max_attempts=_parse_int(
                "AUTH_MAX_ATTEMPTS", DEFAULT_AUTH_MAX_ATTEMPTS, min_value=1
            ),
            auth_lockout_seconds=_parse_int(
                "AUTH_LOCKOUT_SECONDS", DEFAULT_AUTH_LOCKOUT_SECONDS, min_value=1
            ),
            auth_max_tracked_keys=_parse_int(
                "AUTH_MAX_TRACKED_KEYS", DEFAULT_AUTH_MAX_TRACKED_KEYS, min_value=1
            ),
            signup_max_events=_parse_int(
                "SIGNUP_RATE_LIMIT_MAX_EVENTS", DEFAULT_SIGNUP_MAX_EVENTS, min_value=1
            ),
            signup_window_seconds=_parse_int(
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
            temperature=_parse_float(
                "SLM_TEMPERATURE",
                DEFAULT_SLM_TEMPERATURE,
                min_value=0.0,
                max_value=2.0,
            ),
            timeout_seconds=_parse_float(
                "SLM_TIMEOUT_SECONDS",
                DEFAULT_SLM_TIMEOUT_SECONDS,
                min_value=0.1,
                fallback_env_name="SLM_TIMEOUT",
            ),
        ),
        quiz=QuizConfig(
            max_retries=_parse_int(
                "QUIZ_MAX_RETRIES", DEFAULT_QUIZ_MAX_RETRIES, min_value=1
            ),
        ),
    )
    return _settings_instance
