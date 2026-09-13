"""Settings builder, parser, and cached accessor for TutorBox."""

import os

from core.config.captive_settings import build_captive_portal_config
from core.config.constants import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    DEFAULT_BCRYPT_ROUNDS,
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_QUIZ_MAX_RETRIES,
    DEFAULT_SEED_TEACHER_PIN,
    DEFAULT_SEED_TEACHER_USERNAME,
    DEFAULT_SIGNUP_MAX_EVENTS,
    DEFAULT_SIGNUP_WINDOW_SECONDS,
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)
from core.config.models import (
    DatabaseConfig,
    LLMConfig,
    QuizConfig,
    SecurityConfig,
    Settings,
    TTSConfig,
)
from core.config.parsers import parse_bool, parse_db_path, parse_float, parse_int

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
            seed_teacher_username=os.environ.get(
                "SEED_TEACHER_USERNAME", DEFAULT_SEED_TEACHER_USERNAME
            ),
            seed_teacher_pin=os.environ.get(
                "SEED_TEACHER_PIN", DEFAULT_SEED_TEACHER_PIN
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
        tts=TTSConfig(
            enabled=parse_bool("TTS_ENABLED", DEFAULT_TTS_ENABLED),
            binary=os.environ.get("TTS_ESPEAK_BINARY", DEFAULT_TTS_BINARY).strip(),
            voice=os.environ.get("TTS_VOICE") or DEFAULT_TTS_VOICE,
            voice_quc=os.environ.get("TTS_VOICE_QUC", DEFAULT_TTS_VOICE_QUC).strip(),
            words_per_minute=parse_int(
                "TTS_WORDS_PER_MINUTE",
                DEFAULT_TTS_WORDS_PER_MINUTE,
                min_value=80,
                max_value=450,
            ),
            pitch=parse_int("TTS_PITCH", DEFAULT_TTS_PITCH, min_value=0, max_value=99),
            amplitude=parse_int(
                "TTS_AMPLITUDE", DEFAULT_TTS_AMPLITUDE, min_value=0, max_value=200
            ),
            timeout_seconds=parse_float(
                "TTS_TIMEOUT_SECONDS", DEFAULT_TTS_TIMEOUT_SECONDS, min_value=0.5
            ),
            max_chars=parse_int(
                "TTS_MAX_CHARS", DEFAULT_TTS_MAX_CHARS, min_value=40, max_value=5000
            ),
        ),
        captive_portal=build_captive_portal_config(),
    )
    return _settings_instance
