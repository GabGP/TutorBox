"""Unit tests for the environment file loader (src/config/env_loader.py)."""

import os
from pathlib import Path

from config.env_loader import load_env_file


def test_load_env_file_parses_valid_key_values(tmp_path: Path, monkeypatch) -> None:
    """Verifies parsing of comments, quotes, whitespace, and clean values."""
    env_content = """
    # This is a comment
    TEST_ENV_VAR_PLAIN=hello_world
    TEST_ENV_VAR_DOUBLE="double_quoted_value"
    TEST_ENV_VAR_SINGLE='single_quoted_value'
    TEST_ENV_VAR_SPACES = spaced_value

    # Another comment line
    INVALID_LINE_NO_EQUALS
    =NO_KEY_VALUE
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content, encoding="utf-8")

    monkeypatch.delenv("TEST_ENV_VAR_PLAIN", raising=False)
    monkeypatch.delenv("TEST_ENV_VAR_DOUBLE", raising=False)
    monkeypatch.delenv("TEST_ENV_VAR_SINGLE", raising=False)
    monkeypatch.delenv("TEST_ENV_VAR_SPACES", raising=False)

    load_env_file(custom_path=env_file)

    assert os.environ.get("TEST_ENV_VAR_PLAIN") == "hello_world"
    assert os.environ.get("TEST_ENV_VAR_DOUBLE") == "double_quoted_value"
    assert os.environ.get("TEST_ENV_VAR_SINGLE") == "single_quoted_value"
    assert os.environ.get("TEST_ENV_VAR_SPACES") == "spaced_value"


def test_load_env_file_does_not_overwrite_existing_env(
    tmp_path: Path, monkeypatch
) -> None:
    """Verifies that existing environment variables take precedence over .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("PRE_EXISTING_KEY=new_file_value\n", encoding="utf-8")

    monkeypatch.setenv("PRE_EXISTING_KEY", "original_system_value")

    load_env_file(custom_path=env_file)

    assert os.environ.get("PRE_EXISTING_KEY") == "original_system_value"


def test_load_env_file_non_existent_file(tmp_path: Path) -> None:
    """Verifies that loading a non-existent file does not raise an error."""
    non_existent = tmp_path / "does_not_exist.env"
    load_env_file(custom_path=non_existent)


def test_load_env_file_default_search_paths() -> None:
    """Verifies that loading without custom_path executes safely against default paths."""
    load_env_file()
