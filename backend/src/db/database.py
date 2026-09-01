import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / ".cache"
    / "db"
    / "tutorbox.db"
)


DEFAULT_BUSY_TIMEOUT_MS: int = 5000


def get_busy_timeout_ms() -> int:
    """Returns the SQLite busy timeout in milliseconds with environment override."""
    try:
        return int(os.getenv("DB_BUSY_TIMEOUT_MS", str(DEFAULT_BUSY_TIMEOUT_MS)))
    except ValueError:
        return DEFAULT_BUSY_TIMEOUT_MS


def get_db_path() -> str:
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


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
