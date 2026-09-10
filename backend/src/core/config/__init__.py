"""Centralized configuration package for TutorBox."""

from core.config.constants import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    DEFAULT_BCRYPT_ROUNDS,
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_DB_PATH,
    DEFAULT_QUIZ_MAX_RETRIES,
    DEFAULT_SEED_TEACHER_PIN,
    DEFAULT_SEED_TEACHER_USERNAME,
    DEFAULT_SIGNUP_MAX_EVENTS,
    DEFAULT_SIGNUP_WINDOW_SECONDS,
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
    PROJECT_ROOT,
)
from core.config.env_loader import load_env_file
from core.config.models import (
    DatabaseConfig,
    LLMConfig,
    QuizConfig,
    SecurityConfig,
    Settings,
)
from core.config.parsers import (
    parse_db_path,
    parse_float,
    parse_int,
)
from core.config.settings import (
    clear_settings_cache,
    get_settings,
)

__all__ = [
    "DEFAULT_AUTH_LOCKOUT_SECONDS",
    "DEFAULT_AUTH_MAX_ATTEMPTS",
    "DEFAULT_AUTH_MAX_TRACKED_KEYS",
    "DEFAULT_BCRYPT_ROUNDS",
    "DEFAULT_BUSY_TIMEOUT_MS",
    "DEFAULT_DB_PATH",
    "DEFAULT_QUIZ_MAX_RETRIES",
    "DEFAULT_SEED_TEACHER_PIN",
    "DEFAULT_SEED_TEACHER_USERNAME",
    "DEFAULT_SIGNUP_MAX_EVENTS",
    "DEFAULT_SIGNUP_WINDOW_SECONDS",
    "DEFAULT_SLM_BASE_URL",
    "DEFAULT_SLM_MODEL_NAME",
    "DEFAULT_SLM_TEMPERATURE",
    "DEFAULT_SLM_TIMEOUT_SECONDS",
    "PROJECT_ROOT",
    "DatabaseConfig",
    "LLMConfig",
    "QuizConfig",
    "SecurityConfig",
    "Settings",
    "clear_settings_cache",
    "get_settings",
    "load_env_file",
    "parse_db_path",
    "parse_float",
    "parse_int",
]
