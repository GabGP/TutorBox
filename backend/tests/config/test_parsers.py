"""Unit tests for configuration environment parsers (src/config/parsers.py)."""

from pathlib import Path

from config.constants import DEFAULT_DB_PATH, PROJECT_ROOT
from config.parsers import parse_db_path, parse_float, parse_int


def test_parse_db_path_none_and_empty() -> None:
    """Verifies that parse_db_path returns DEFAULT_DB_PATH when None or empty."""
    assert parse_db_path(None) == DEFAULT_DB_PATH
    assert parse_db_path("") == DEFAULT_DB_PATH


def test_parse_db_path_memory() -> None:
    """Verifies that parse_db_path preserves :memory: identifier."""
    assert parse_db_path(":memory:") == ":memory:"


def test_parse_db_path_absolute(tmp_path: Path) -> None:
    """Verifies that parse_db_path preserves absolute filesystem paths."""
    abs_path = str(tmp_path / "custom.db")
    assert parse_db_path(abs_path) == abs_path


def test_parse_db_path_relative() -> None:
    """Verifies that relative paths are normalized against PROJECT_ROOT."""
    rel_path = ".cache/db/tutorbox.db"
    expected = str((PROJECT_ROOT / rel_path).resolve())
    assert parse_db_path(rel_path) == expected


def test_parse_int_normal_and_fallbacks(monkeypatch) -> None:
    """Verifies parse_int with valid values, missing env, invalid formats, and bounds."""
    # Unset env var returns default
    monkeypatch.delenv("TEST_INT_VAR", raising=False)
    assert parse_int("TEST_INT_VAR", 42) == 42

    # Valid value
    monkeypatch.setenv("TEST_INT_VAR", "100")
    assert parse_int("TEST_INT_VAR", 42) == 100

    # Non-integer value falls back to default
    monkeypatch.setenv("TEST_INT_VAR", "not_a_number")
    assert parse_int("TEST_INT_VAR", 42) == 42

    # Min bound violation
    monkeypatch.setenv("TEST_INT_VAR", "3")
    assert parse_int("TEST_INT_VAR", 42, min_value=5) == 42

    # Max bound violation
    monkeypatch.setenv("TEST_INT_VAR", "20")
    assert parse_int("TEST_INT_VAR", 42, max_value=10) == 42


def test_parse_float_normal_and_fallbacks(monkeypatch) -> None:
    """Verifies parse_float with valid values, missing env, fallback keys, invalid formats, and bounds."""
    # Unset env var returns default
    monkeypatch.delenv("TEST_FLOAT_VAR", raising=False)
    monkeypatch.delenv("TEST_FLOAT_FALLBACK", raising=False)
    assert parse_float("TEST_FLOAT_VAR", 1.5) == 1.5

    # Fallback key used when primary unset
    monkeypatch.setenv("TEST_FLOAT_FALLBACK", "3.14")
    assert (
        parse_float("TEST_FLOAT_VAR", 1.5, fallback_env_name="TEST_FLOAT_FALLBACK")
        == 3.14
    )

    # Primary key takes precedence
    monkeypatch.setenv("TEST_FLOAT_VAR", "2.71")
    assert (
        parse_float("TEST_FLOAT_VAR", 1.5, fallback_env_name="TEST_FLOAT_FALLBACK")
        == 2.71
    )

    # Invalid float string falls back to default
    monkeypatch.setenv("TEST_FLOAT_VAR", "invalid_float")
    assert parse_float("TEST_FLOAT_VAR", 1.5) == 1.5

    # Min bound violation
    monkeypatch.setenv("TEST_FLOAT_VAR", "0.05")
    assert parse_float("TEST_FLOAT_VAR", 1.5, min_value=0.1) == 1.5

    # Max bound violation
    monkeypatch.setenv("TEST_FLOAT_VAR", "5.0")
    assert parse_float("TEST_FLOAT_VAR", 1.5, max_value=2.0) == 1.5
