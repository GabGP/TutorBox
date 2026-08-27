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
