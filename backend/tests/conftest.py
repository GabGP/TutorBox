import os
import sqlite3
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db.migrations import apply_migrations
from src.main import app
from src.security.auth import hash_pin


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    Ensure rate limiter state is clean before and after every test.
    """
    from src.security.rate_limit import login_rate_limiter

    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


@pytest.fixture
def temp_db():
    """
    Creates an isolated temporary SQLite database with all migrations applied.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    os.environ["DATABASE_PATH"] = db_path
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    yield db_path, conn

    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def seeded_db(temp_db):
    """
    Pre-seeds a test user: username='student1', pin='1234'.
    """
    db_path, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin) VALUES (?, ?)",
        ("student1", hashed),
    )
    conn.commit()
    return db_path, conn


@pytest.fixture
def client():
    """
    TestClient that uses whatever DATABASE_PATH is currently set.
    Must be used AFTER a DB fixture (temp_db or seeded_db) in the test signature.
    """
    with TestClient(app) as test_client:
        yield test_client
