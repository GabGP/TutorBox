"""Unit tests for centralized typed settings (src/config/settings.py)."""

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
    PROJECT_ROOT,
)
from config.settings import (
    clear_settings_cache,
    get_settings,
)


def test_default_settings(monkeypatch) -> None:
    """Verifies that all domain settings fall back to default constants when env is empty."""
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("DB_BUSY_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("BCRYPT_ROUNDS", raising=False)
    monkeypatch.delenv("AUTH_MAX_ATTEMPTS", raising=False)
    monkeypatch.delenv("AUTH_LOCKOUT_SECONDS", raising=False)
    monkeypatch.delenv("AUTH_MAX_TRACKED_KEYS", raising=False)
    monkeypatch.delenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", raising=False)
    monkeypatch.delenv("SIGNUP_RATE_LIMIT_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("SLM_BASE_URL", raising=False)
    monkeypatch.delenv("SLM_MODEL_NAME", raising=False)
    monkeypatch.delenv("SLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("SLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("SLM_TIMEOUT", raising=False)
    monkeypatch.delenv("QUIZ_MAX_RETRIES", raising=False)

    clear_settings_cache()
    settings = get_settings()

    # Database
    assert settings.database.database_path == DEFAULT_DB_PATH
    assert settings.database.busy_timeout_ms == DEFAULT_BUSY_TIMEOUT_MS

    # Security
    assert settings.security.bcrypt_rounds == DEFAULT_BCRYPT_ROUNDS
    assert settings.security.auth_max_attempts == DEFAULT_AUTH_MAX_ATTEMPTS
    assert settings.security.auth_lockout_seconds == DEFAULT_AUTH_LOCKOUT_SECONDS
    assert settings.security.auth_max_tracked_keys == DEFAULT_AUTH_MAX_TRACKED_KEYS
    assert settings.security.signup_max_events == DEFAULT_SIGNUP_MAX_EVENTS
    assert settings.security.signup_window_seconds == DEFAULT_SIGNUP_WINDOW_SECONDS

    # LLM
    assert settings.llm.base_url == DEFAULT_SLM_BASE_URL
    assert settings.llm.model_name == DEFAULT_SLM_MODEL_NAME
    assert settings.llm.temperature == DEFAULT_SLM_TEMPERATURE
    assert settings.llm.timeout_seconds == DEFAULT_SLM_TIMEOUT_SECONDS

    # Quiz
    assert settings.quiz.max_retries == DEFAULT_QUIZ_MAX_RETRIES


def test_database_settings_env_overrides(monkeypatch) -> None:
    """Verifies environment overrides and fallback on invalid numeric value for database."""
    monkeypatch.setenv("DATABASE_PATH", "/tmp/custom.db")
    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", "8000")

    clear_settings_cache()
    settings = get_settings()
    assert settings.database.database_path == "/tmp/custom.db"
    assert settings.database.busy_timeout_ms == 8000

    # Fallback on invalid int
    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", "invalid_int")
    clear_settings_cache()
    assert get_settings().database.busy_timeout_ms == DEFAULT_BUSY_TIMEOUT_MS


def test_database_settings_relative_and_memory(monkeypatch) -> None:
    """Verifies that relative DATABASE_PATH resolves to PROJECT_ROOT and :memory: is kept."""
    monkeypatch.setenv("DATABASE_PATH", ".cache/db/tutorbox.db")
    clear_settings_cache()
    assert get_settings().database.database_path == str(
        (PROJECT_ROOT / ".cache/db/tutorbox.db").resolve()
    )

    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    clear_settings_cache()
    assert get_settings().database.database_path == ":memory:"


def test_security_settings_env_overrides(monkeypatch) -> None:
    """Verifies environment overrides and fallback on invalid numeric values for security."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    monkeypatch.setenv("AUTH_MAX_ATTEMPTS", "10")
    monkeypatch.setenv("AUTH_LOCKOUT_SECONDS", "60")
    monkeypatch.setenv("AUTH_MAX_TRACKED_KEYS", "5000")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", "50")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_WINDOW_SECONDS", "120")

    clear_settings_cache()
    settings = get_settings()
    assert settings.security.bcrypt_rounds == 4
    assert settings.security.auth_max_attempts == 10
    assert settings.security.auth_lockout_seconds == 60
    assert settings.security.auth_max_tracked_keys == 5000
    assert settings.security.signup_max_events == 50
    assert settings.security.signup_window_seconds == 120

    # Fallback on invalid values
    monkeypatch.setenv("BCRYPT_ROUNDS", "invalid")
    monkeypatch.setenv("AUTH_MAX_ATTEMPTS", "invalid")
    monkeypatch.setenv("AUTH_LOCKOUT_SECONDS", "invalid")
    monkeypatch.setenv("AUTH_MAX_TRACKED_KEYS", "invalid")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", "invalid")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_WINDOW_SECONDS", "invalid")

    clear_settings_cache()
    fallback_settings = get_settings()
    assert fallback_settings.security.bcrypt_rounds == DEFAULT_BCRYPT_ROUNDS
    assert fallback_settings.security.auth_max_attempts == DEFAULT_AUTH_MAX_ATTEMPTS
    assert (
        fallback_settings.security.auth_lockout_seconds == DEFAULT_AUTH_LOCKOUT_SECONDS
    )
    assert (
        fallback_settings.security.auth_max_tracked_keys
        == DEFAULT_AUTH_MAX_TRACKED_KEYS
    )
    assert fallback_settings.security.signup_max_events == DEFAULT_SIGNUP_MAX_EVENTS
    assert (
        fallback_settings.security.signup_window_seconds
        == DEFAULT_SIGNUP_WINDOW_SECONDS
    )


def test_llm_settings_env_overrides(monkeypatch) -> None:
    """Verifies LLM environment overrides, trailing slash stripping, and timeout fallback."""
    monkeypatch.setenv("SLM_BASE_URL", "http://10.0.0.99:11434/v1/")
    monkeypatch.setenv("SLM_MODEL_NAME", "qwen2.5:3b")
    monkeypatch.setenv("SLM_TEMPERATURE", "0.65")
    monkeypatch.setenv("SLM_TIMEOUT_SECONDS", "45.0")

    clear_settings_cache()
    settings = get_settings()
    assert settings.llm.base_url == "http://10.0.0.99:11434/v1"
    assert settings.llm.model_name == "qwen2.5:3b"
    assert settings.llm.temperature == 0.65
    assert settings.llm.timeout_seconds == 45.0

    # Fallback to SLM_TIMEOUT if SLM_TIMEOUT_SECONDS is not set
    monkeypatch.delenv("SLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("SLM_TIMEOUT", "90.5")
    clear_settings_cache()
    assert get_settings().llm.timeout_seconds == 90.5

    # Fallback on invalid floats
    monkeypatch.setenv("SLM_TEMPERATURE", "invalid_float")
    monkeypatch.setenv("SLM_TIMEOUT_SECONDS", "invalid_float")
    clear_settings_cache()
    fallback_settings = get_settings()
    assert fallback_settings.llm.temperature == DEFAULT_SLM_TEMPERATURE
    assert fallback_settings.llm.timeout_seconds == DEFAULT_SLM_TIMEOUT_SECONDS


def test_quiz_settings_env_overrides(monkeypatch) -> None:
    """Verifies quiz settings environment overrides and fallback on invalid values."""
    monkeypatch.setenv("QUIZ_MAX_RETRIES", "5")
    clear_settings_cache()
    assert get_settings().quiz.max_retries == 5

    monkeypatch.setenv("QUIZ_MAX_RETRIES", "invalid_number")
    clear_settings_cache()
    assert get_settings().quiz.max_retries == DEFAULT_QUIZ_MAX_RETRIES


def test_settings_range_validation_fallbacks(monkeypatch) -> None:
    """Verifies that out-of-range numeric values and empty strings fall back to defaults."""
    # Min value bounds
    monkeypatch.setenv("QUIZ_MAX_RETRIES", "0")
    monkeypatch.setenv("BCRYPT_ROUNDS", "2")
    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", "-500")
    monkeypatch.setenv("AUTH_MAX_ATTEMPTS", "0")
    monkeypatch.setenv("SLM_TEMPERATURE", "-0.5")
    monkeypatch.setenv("SLM_TIMEOUT_SECONDS", "0.0")

    clear_settings_cache()
    settings = get_settings()
    assert settings.quiz.max_retries == DEFAULT_QUIZ_MAX_RETRIES
    assert settings.security.bcrypt_rounds == DEFAULT_BCRYPT_ROUNDS
    assert settings.database.busy_timeout_ms == DEFAULT_BUSY_TIMEOUT_MS
    assert settings.security.auth_max_attempts == DEFAULT_AUTH_MAX_ATTEMPTS
    assert settings.llm.temperature == DEFAULT_SLM_TEMPERATURE
    assert settings.llm.timeout_seconds == DEFAULT_SLM_TIMEOUT_SECONDS

    # Max value bounds
    monkeypatch.setenv("BCRYPT_ROUNDS", "35")
    monkeypatch.setenv("SLM_TEMPERATURE", "2.5")
    clear_settings_cache()
    max_settings = get_settings()
    assert max_settings.security.bcrypt_rounds == DEFAULT_BCRYPT_ROUNDS
    assert max_settings.llm.temperature == DEFAULT_SLM_TEMPERATURE

    # Empty string overrides
    monkeypatch.setenv("DATABASE_PATH", "")
    monkeypatch.setenv("SLM_BASE_URL", "")
    monkeypatch.setenv("SLM_MODEL_NAME", "")
    clear_settings_cache()
    empty_settings = get_settings()
    assert empty_settings.database.database_path == DEFAULT_DB_PATH
    assert empty_settings.llm.base_url == DEFAULT_SLM_BASE_URL
    assert empty_settings.llm.model_name == DEFAULT_SLM_MODEL_NAME


def test_clear_settings_cache_and_caching(monkeypatch) -> None:
    """Verifies caching behavior of get_settings and clear_settings_cache."""
    clear_settings_cache()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

    clear_settings_cache()
    s3 = get_settings()
    assert s3 is not s1

    # Reload argument forces fresh instance
    s4 = get_settings(reload=True)
    assert s4 is not s3
