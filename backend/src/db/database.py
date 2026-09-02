import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from config import DEFAULT_BUSY_TIMEOUT_MS, DEFAULT_DB_PATH, get_settings

__all__ = [
    "DEFAULT_BUSY_TIMEOUT_MS",
    "DEFAULT_DB_PATH",
    "get_busy_timeout_ms",
    "get_db",
    "get_db_connection",
    "get_db_path",
]


def get_busy_timeout_ms() -> int:
    """Returns the SQLite busy timeout in milliseconds with environment override."""
    return get_settings(reload=True).database.busy_timeout_ms


def get_db_path() -> str:
    """Returns the SQLite database file path with environment override."""
    return get_settings(reload=True).database.database_path


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    if target_path != ":memory:":
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute(f"PRAGMA busy_timeout = {get_busy_timeout_ms()};")
    return conn


@contextmanager
def get_db(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that guarantees the SQLite connection is closed,
    even if an exception occurs during the request.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
