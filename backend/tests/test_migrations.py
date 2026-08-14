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
        cursor.execute("SELECT version FROM schema_migrations WHERE version = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1
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
        cursor.execute("SELECT version, applied_at FROM schema_migrations")
        rows = cursor.fetchall()
        assert len(rows) >= 1
        assert rows[0][0] == 1
        assert rows[0][1] is not None
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
