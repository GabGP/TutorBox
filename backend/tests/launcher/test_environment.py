"""Unit tests for the Utz'tutor launcher environment helpers (tools/launcher/environment.py)."""

import os

from tools.launcher import environment, paths


def _keep_key_unset_after_test(monkeypatch, name):
    """Clears name from os.environ and registers its restoration so writes cannot leak."""
    monkeypatch.setenv(name, "placeholder")
    monkeypatch.delenv(name)


def test_load_env_loads_valid_key_values(tmp_path, monkeypatch):
    """Verifies load_env populates os.environ without overwriting existing keys."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MOCK_KEY_ONE=alpha\n# comment\nMOCK_KEY_TWO='beta'\n", encoding="utf-8"
    )
    _keep_key_unset_after_test(monkeypatch, "MOCK_KEY_ONE")
    _keep_key_unset_after_test(monkeypatch, "MOCK_KEY_TWO")

    environment.load_env(env_file)
    assert os.environ.get("MOCK_KEY_ONE") == "alpha"
    assert os.environ.get("MOCK_KEY_TWO") == "beta"


def test_load_env_missing_file_is_noop(tmp_path, monkeypatch):
    """Verifies load_env returns quietly and sets nothing when the env file is absent."""
    _keep_key_unset_after_test(monkeypatch, "MOCK_MISSING_FILE_KEY")

    environment.load_env(tmp_path / "does-not-exist.env")
    assert "MOCK_MISSING_FILE_KEY" not in os.environ


def test_load_env_keeps_existing_environment_value(tmp_path, monkeypatch):
    """Verifies load_env never overwrites a key already defined in os.environ."""
    monkeypatch.setenv("MOCK_PRESET_KEY", "original")
    env_file = tmp_path / ".env"
    env_file.write_text("MOCK_PRESET_KEY=replacement\n", encoding="utf-8")

    environment.load_env(env_file)
    assert os.environ["MOCK_PRESET_KEY"] == "original"


def test_load_env_skips_blank_comment_and_invalid_lines(tmp_path, monkeypatch):
    """Verifies load_env ignores blank lines, comment lines and lines without '='."""
    for name in ("MOCK_COMMENTED_KEY", "MOCK_INVALID_LINE", "MOCK_VALID_KEY"):
        _keep_key_unset_after_test(monkeypatch, name)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n   \n# MOCK_COMMENTED_KEY=hidden\nMOCK_INVALID_LINE\nMOCK_VALID_KEY=shown\n",
        encoding="utf-8",
    )

    environment.load_env(env_file)
    assert "MOCK_COMMENTED_KEY" not in os.environ
    assert "MOCK_INVALID_LINE" not in os.environ
    assert os.environ["MOCK_VALID_KEY"] == "shown"


def test_resolve_venv_path_defaults_when_variable_unset(monkeypatch):
    """Verifies resolve_venv_path returns the default .cache/venv when unset."""
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    assert environment.resolve_venv_path() == paths.DEFAULT_VENV_DIR


def test_resolve_venv_path_keeps_absolute_variable(tmp_path, monkeypatch):
    """Verifies resolve_venv_path returns an absolute UV_PROJECT_ENVIRONMENT unchanged."""
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(tmp_path))

    resolved = environment.resolve_venv_path()
    assert resolved == tmp_path
    assert resolved.is_absolute()


def test_resolve_venv_path_resolves_relative_against_root(monkeypatch):
    """Verifies resolve_venv_path resolves a relative value against ROOT_DIR."""
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "custom/venv")

    resolved = environment.resolve_venv_path()
    assert resolved.is_absolute()
    assert resolved == (paths.ROOT_DIR / "custom" / "venv").resolve()
