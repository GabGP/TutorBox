"""Configuration value parsers and sanitizers for environment variables."""

import os

from config.constants import DEFAULT_DB_PATH, PROJECT_ROOT

__all__ = ["parse_db_path", "parse_float", "parse_int"]


def parse_db_path(raw_path: str | None) -> str:
    """
    Parses database path, resolving relative paths against PROJECT_ROOT.

    Preserves in-memory identifiers and absolute paths without modification.
    """
    if not raw_path:
        return DEFAULT_DB_PATH
    if raw_path == ":memory:":
        return ":memory:"
    if os.path.isabs(raw_path):
        return raw_path
    return str((PROJECT_ROOT / raw_path).resolve())


def parse_int(
    env_var_name: str,
    default_value: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Parses an integer environment variable with bounds validation and fallback."""
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


def parse_float(
    env_var_name: str,
    default_value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    fallback_env_name: str | None = None,
) -> float:
    """Parses a float environment variable with fallback names, bounds, and defaults."""
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
