import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "tutorbox.db")


def get_db_path() -> str:
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
