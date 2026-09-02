"""Typed domain configuration data models for TutorBox."""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class DatabaseConfig:
    database_path: str = DEFAULT_DB_PATH
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS


@dataclass(frozen=True)
class SecurityConfig:
    bcrypt_rounds: int = DEFAULT_BCRYPT_ROUNDS
    auth_max_attempts: int = DEFAULT_AUTH_MAX_ATTEMPTS
    auth_lockout_seconds: int = DEFAULT_AUTH_LOCKOUT_SECONDS
    auth_max_tracked_keys: int = DEFAULT_AUTH_MAX_TRACKED_KEYS
    signup_max_events: int = DEFAULT_SIGNUP_MAX_EVENTS
    signup_window_seconds: int = DEFAULT_SIGNUP_WINDOW_SECONDS


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = DEFAULT_SLM_BASE_URL
    model_name: str = DEFAULT_SLM_MODEL_NAME
    temperature: float = DEFAULT_SLM_TEMPERATURE
    timeout_seconds: float = DEFAULT_SLM_TIMEOUT_SECONDS


@dataclass(frozen=True)
class QuizConfig:
    max_retries: int = DEFAULT_QUIZ_MAX_RETRIES


@dataclass(frozen=True)
class Settings:
    database: DatabaseConfig
    security: SecurityConfig
    llm: LLMConfig
    quiz: QuizConfig
