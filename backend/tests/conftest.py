import os
import shutil
import sqlite3
import sys
import tempfile

# Use minimum work factor for fast test execution (240x speedup)
os.environ["BCRYPT_ROUNDS"] = "4"

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db_connection
from src.db.migrations import apply_migrations
from src.main import app
from src.security.auth import hash_pin

# Cache pre-hashed default test PIN ('1234') across fixtures
PRE_HASHED_PIN_1234 = hash_pin("1234")


@pytest.fixture(scope="session")
def _migrated_template_db(tmp_path_factory: pytest.TempPathFactory) -> str:
    """
    Creates a single migrated SQLite template database per test session/worker.
    Individual tests copy this template in <1ms instead of reapplying migrations.
    """
    temp_dir = tmp_path_factory.mktemp("db_template")
    template_path = str(temp_dir / "template.db")
    apply_migrations(template_path)
    return template_path


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """
    Ensure rate limiter state is clean before and after every test across all import aliases.
    """

    def _clear_all():
        for mod_name in ("security.rate_limit", "src.security.rate_limit"):
            mod = sys.modules.get(mod_name)
            if mod:
                if hasattr(mod, "login_rate_limiter"):
                    mod.login_rate_limiter.clear()
                if hasattr(mod, "signup_rate_limiter"):
                    mod.signup_rate_limiter.clear()

    _clear_all()
    yield
    _clear_all()


@pytest.fixture
def temp_db(monkeypatch: pytest.MonkeyPatch, _migrated_template_db: str):
    """
    Creates an isolated temporary SQLite database with all migrations applied.
    Uses monkeypatch for DATABASE_PATH so the environment is always restored,
    even if the test fails.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    shutil.copyfile(_migrated_template_db, db_path)

    monkeypatch.setenv("DATABASE_PATH", db_path)

    conn = get_db_connection(db_path)

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
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin) VALUES (?, ?)",
        ("student1", PRE_HASHED_PIN_1234),
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


@pytest.fixture
def staff_db(temp_db):
    """
    Pre-seeds standard test roster across all roles:
    - student1 (pin: 1234, role: student)
    - student2 (pin: 1234, role: student)
    - teacher1 (pin: 1234, role: teacher)
    - admin1   (pin: 1234, role: admin)
    """
    db_path, conn = temp_db
    cursor = conn.cursor()
    users = [
        ("student1", PRE_HASHED_PIN_1234, "student"),
        ("student2", PRE_HASHED_PIN_1234, "student"),
        ("teacher1", PRE_HASHED_PIN_1234, "teacher"),
        ("admin1", PRE_HASHED_PIN_1234, "admin"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
        users,
    )
    conn.commit()
    return db_path, conn


def auth_headers(
    client: TestClient, username: str, pin: str = "1234"
) -> dict[str, str]:
    """Helper to log in and return Bearer authorization headers."""
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "pin": pin}
    )
    assert response.status_code == 200, (
        f"Login failed for {username}: {response.json()}"
    )
    return {"Authorization": f"Bearer {response.json()['session_id']}"}


def get_user_id(conn: sqlite3.Connection, username: str) -> int:
    """Helper to query user id by username."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    assert row is not None, f"User {username} not found in test database."
    return row["id"]
