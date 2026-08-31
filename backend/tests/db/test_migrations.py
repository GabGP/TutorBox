import os
import sqlite3
import tempfile

from src.db.migrations import apply_migrations


def test_migrations_applied_successfully():
    """
    Test that running apply_migrations builds the schema from scratch.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        apply_migrations(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        rows = cursor.fetchall()
        versions = [r[0] for r in rows]
        assert 1 in versions
        assert 2 in versions
        assert 3 in versions
        assert 4 in versions
        assert 5 in versions
        assert 6 in versions
        assert 7 in versions
        assert 8 in versions

        # Verify columns added by migrations 002, 004, 005 exist on users
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1] for col in cursor.fetchall()}
        assert "role" in columns
        assert "must_change_pin" in columns
        assert "deleted_at" in columns
        assert "former_username" in columns

        # Verify FK lookup indexes added by migration 003 exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_turn_logs_session_id'"
        )
        assert cursor.fetchone() is not None

        # Verify audit_logs table and indexes added by migration 006 exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_audit_logs_actor'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_audit_logs_target'"
        )
        assert cursor.fetchone() is not None

        # Verify devices table and index added by migration 007 exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='devices'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_devices_assigned_user'"
        )
        assert cursor.fetchone() is not None

        # Verify quiz_questions table and indexes added by migration 008 exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_questions'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quiz_questions_topic'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quiz_questions_created'"
        )
        assert cursor.fetchone() is not None
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migrations_are_idempotent():
    """
    Test that running apply_migrations multiple times does not crash and preserves schema.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Run first time
        apply_migrations(db_path)
        # Run second time (idempotency check)
        apply_migrations(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = 1")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migrations_records_version():
    """
    Test that schema_migrations records the migration version and timestamp.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        apply_migrations(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT version, applied_at FROM schema_migrations ORDER BY version"
        )
        rows = cursor.fetchall()
        assert len(rows) >= 1
        assert rows[0][0] == 1
        assert rows[0][1] is not None
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migrations_missing_directory():
    """
    Test that apply_migrations handles a missing migrations directory gracefully.
    """
    from pathlib import Path
    from unittest.mock import patch

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        with patch(
            "src.db.migrations.get_migrations_dir",
            return_value=Path("/non_existent_dir_12345"),
        ):
            apply_migrations(db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            assert "schema_migrations" in tables
            assert "users" not in tables
            conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migrations_invalid_filename_skipped(tmp_path):
    """
    Test that files with invalid naming formats are skipped without raising errors.
    """
    from unittest.mock import patch

    db_path = str(tmp_path / "test_invalid_mig.db")
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()

    # Create invalid migration file
    (mig_dir / "invalid_name.sql").write_text(
        "CREATE TABLE test (id INT);", encoding="utf-8"
    )
    # Create valid migration file
    (mig_dir / "001_valid.sql").write_text(
        "CREATE TABLE valid_table (id INT);", encoding="utf-8"
    )

    with patch("src.db.migrations.get_migrations_dir", return_value=mig_dir):
        apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations")
    versions = [r[0] for r in cursor.fetchall()]
    assert versions == [1]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    assert "valid_table" in tables
    assert "test" not in tables
    conn.close()


def test_migrations_skip_duplicate_version_numbers(tmp_path):
    """
    Test that two files claiming the same version do not crash: the first is
    applied and the second is skipped with a warning.
    """
    from unittest.mock import patch

    db_path = str(tmp_path / "dup.db")
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()

    (mig_dir / "001_first.sql").write_text(
        "CREATE TABLE first_table (id INT);", encoding="utf-8"
    )
    (mig_dir / "001_second.sql").write_text(
        "CREATE TABLE second_table (id INT);", encoding="utf-8"
    )

    with patch("src.db.migrations.get_migrations_dir", return_value=mig_dir):
        apply_migrations(db_path)  # must not raise

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = 1")
    assert cursor.fetchone()[0] == 1
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "first_table" in tables
    assert "second_table" not in tables
    conn.close()


def test_migrations_rollback_on_failure(tmp_path):
    """
    Test that if a statement in a migration fails, the transaction is rolled back
    and the version is not recorded in schema_migrations.
    """
    from unittest.mock import patch

    import pytest

    db_path = str(tmp_path / "test_rollback.db")
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()

    # Create a migration that partially succeeds then fails
    (mig_dir / "001_fail.sql").write_text(
        "CREATE TABLE table_before_fail (id INT); INVALID SQL SYNTAX ERROR;",
        encoding="utf-8",
    )

    with (
        patch("src.db.migrations.get_migrations_dir", return_value=mig_dir),
        pytest.raises(sqlite3.OperationalError),
    ):
        apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Version 1 should NOT be recorded
    cursor.execute("SELECT version FROM schema_migrations WHERE version = 1")
    assert cursor.fetchone() is None

    # Table created before error should have been rolled back
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    assert "table_before_fail" not in tables
    conn.close()
