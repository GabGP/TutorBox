from src.db.database import get_db_connection


def test_database_connection(temp_db):
    """
    Test that database connection opens successfully and returns valid connection.
    """
    db_path, _ = temp_db
    conn = get_db_connection(db_path)
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1
    conn.close()


def test_foreign_keys_pragma_enabled(temp_db):
    """
    Test that PRAGMA foreign_keys is enabled on database connections.
    """
    db_path, _ = temp_db
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    result = cursor.fetchone()
    assert result[0] == 1
    conn.close()


def test_sqlite_pragmas_enabled(temp_db):
    """
    Test that all required SQLite engine PRAGMAs are active on connections:
    - foreign_keys = ON (1)
    - journal_mode = WAL ('wal')
    - busy_timeout = 5000 (5000)
    """
    db_path, _ = temp_db
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys;")
    assert cursor.fetchone()[0] == 1

    cursor.execute("PRAGMA journal_mode;")
    assert cursor.fetchone()[0].lower() == "wal"

    cursor.execute("PRAGMA busy_timeout;")
    assert cursor.fetchone()[0] == 5000

    conn.close()


def test_database_tables_exist(temp_db):
    """
    Test that all required schema tables exist in the database.
    """
    _, conn = temp_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row["name"] for row in cursor.fetchall()}

    expected_tables = {"schema_migrations", "users", "sessions", "turn_logs"}
    assert expected_tables.issubset(tables)


def test_default_db_path_points_to_root_cache_dir(monkeypatch):
    """
    Test that get_db_path defaults to <repo-root>/.cache/db/tutorbox.db when env var is unset.
    """
    from pathlib import Path

    from src.db.database import DEFAULT_DB_PATH, get_db_path

    monkeypatch.delenv("DATABASE_PATH", raising=False)
    resolved_path = get_db_path()
    assert resolved_path == DEFAULT_DB_PATH
    expected_suffix = str(Path(".cache") / "db" / "tutorbox.db")
    assert resolved_path.endswith(expected_suffix)


def test_get_db_connection_auto_creates_parent_directories(tmp_path):
    """
    Test that get_db_connection automatically creates non-existent parent directories.
    """
    nested_db_path = str(tmp_path / "deep" / "nested" / "cache" / "test.db")
    conn = get_db_connection(nested_db_path)
    try:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()


def test_get_db_connection_memory():
    """
    Test that get_db_connection handles :memory: databases without filesystem errors.
    """
    conn = get_db_connection(":memory:")
    try:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()


def test_get_db_context_manager(temp_db):
    """
    Test that get_db context manager yields open connection and closes it upon exit.
    """
    from src.db.database import get_db

    db_path, _ = temp_db
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1


def test_busy_timeout_env_and_fallback(monkeypatch):
    """
    Test that get_busy_timeout_ms respects environment override and falls back on invalid values.
    """
    from src.db.database import DEFAULT_BUSY_TIMEOUT_MS, get_busy_timeout_ms

    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", "8000")
    assert get_busy_timeout_ms() == 8000

    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", "not_a_number")
    assert get_busy_timeout_ms() == DEFAULT_BUSY_TIMEOUT_MS
