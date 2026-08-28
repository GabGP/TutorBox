import logging

from fastapi.testclient import TestClient

from src.db.database import get_db_connection
from src.security.auth import hash_pin
from src.security.rate_limit import LOCKOUT_DURATION_SECONDS


def test_login_success(seeded_db, client: TestClient):
    """
    Test successful student login returns 200 OK and session_id.
    """
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["username"] == "student1"
    assert data["status"] == "authenticated"


def test_login_incorrect_pin(seeded_db, client: TestClient):
    """
    Test login with incorrect PIN returns 401 Unauthorized.
    """
    response = client.post("/login", json={"username": "student1", "pin": "9999"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid username or PIN."


def test_login_user_not_found(seeded_db, client: TestClient):
    """
    Test login with non-existent user returns 401 Unauthorized.
    """
    response = client.post("/login", json={"username": "unknown_user", "pin": "1234"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid username or PIN."


def test_login_creates_database_session(seeded_db, client: TestClient):
    """
    Test that successful login persists an active session row in sessions table.
    """
    db_path, _ = seeded_db
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, is_active FROM sessions WHERE id = ?", (session_id,)
    )
    session = cursor.fetchone()
    assert session is not None
    assert session["id"] == session_id
    assert session["is_active"] == 1
    conn.close()


def test_session_id_never_logged(seeded_db, client: TestClient, caplog):
    """
    SECURITY PROOF 4:
    The session identifier returned to the client must never appear in any
    log output (it is a bearer credential).
    """
    with caplog.at_level(logging.DEBUG):
        response = client.post("/login", json={"username": "student1", "pin": "1234"})

    assert response.status_code == 200
    session_id = response.json()["session_id"]

    for record in caplog.records:
        assert session_id not in record.getMessage(), (
            f"Security violation: session ID leaked in log: '{record.getMessage()}'"
        )


def test_login_rate_limiting_triggers_429(seeded_db, client: TestClient):
    """
    Test that 5 consecutive failed login attempts lock out the user and the 6th returns 429.
    """
    # 5 failed attempts with wrong PIN
    for _ in range(5):
        response = client.post("/login", json={"username": "student1", "pin": "9999"})
        assert response.status_code == 401

    # 6th attempt should be blocked with 429 Too Many Requests
    response = client.post("/login", json={"username": "student1", "pin": "9999"})
    assert response.status_code == 429
    assert "Too many failed login attempts" in response.json()["detail"]

    # Even with correct PIN, user is locked out
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 429


def test_login_rate_limiting_lockout_expires(
    seeded_db, client: TestClient, monkeypatch
):
    """
    Test that after the lockout duration passes, the user can successfully log in.
    """
    import time

    # Trigger lockout
    for _ in range(5):
        client.post("/login", json={"username": "student1", "pin": "9999"})

    # Verify locked out
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 429

    # Advance time past the lockout duration (constant-driven: survives recalibration)
    original_time = time.time()
    monkeypatch.setattr(
        time, "time", lambda: original_time + LOCKOUT_DURATION_SECONDS + 1
    )

    # Now login with correct PIN should succeed
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"


def test_login_rate_limiting_resets_on_success(seeded_db, client: TestClient):
    """
    Test that successful login resets the consecutive failure counter.
    """
    # 4 failed attempts (less than max of 5)
    for _ in range(4):
        response = client.post("/login", json={"username": "student1", "pin": "9999"})
        assert response.status_code == 401

    # Successful login resets the counter
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200

    # 4 more failed attempts shouldn't lock out (needs 5 new consecutive ones)
    for _ in range(4):
        response = client.post("/login", json={"username": "student1", "pin": "9999"})
        assert response.status_code == 401


def test_login_rejects_oversized_username(seeded_db, client: TestClient):
    """
    Usernames longer than 32 characters must fail validation with 422.
    """
    response = client.post("/login", json={"username": "x" * 33, "pin": "1234"})
    assert response.status_code == 422


def test_login_rejects_invalid_username_characters(seeded_db, client: TestClient):
    """
    Usernames with characters outside [A-Za-z0-9_.-] must be rejected
    (log-injection guard).
    """
    response = client.post("/login", json={"username": "bad\nuser", "pin": "1234"})
    assert response.status_code == 422


def test_login_rejects_non_numeric_pin(seeded_db, client: TestClient):
    """
    Pins must be numeric digits only.
    """
    response = client.post("/login", json={"username": "student1", "pin": "abcd"})
    assert response.status_code == 422


def test_login_rejects_wrong_pin_length(seeded_db, client: TestClient):
    """
    Pins shorter than 4 or longer than 8 digits must be rejected.
    """
    short = client.post("/login", json={"username": "student1", "pin": "123"})
    long_pin = client.post("/login", json={"username": "student1", "pin": "1" * 9})
    assert short.status_code == 422
    assert long_pin.status_code == 422


def test_login_response_surfaces_must_change_pin(temp_db, client: TestClient):
    """
    Login must return must_change_pin=True when flagged in the database,
    and must_change_pin=False by default.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, must_change_pin) VALUES (?, ?, 1)",
        ("rotate_user", hashed),
    )
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, must_change_pin) VALUES (?, ?, 0)",
        ("normal_user", hashed),
    )
    conn.commit()

    # User with rotation pending
    res1 = client.post("/login", json={"username": "rotate_user", "pin": "1234"})
    assert res1.status_code == 200
    assert res1.json()["must_change_pin"] is True

    # User with no rotation pending
    res2 = client.post("/login", json={"username": "normal_user", "pin": "1234"})
    assert res2.status_code == 200
    assert res2.json()["must_change_pin"] is False


def test_login_soft_deleted_user_returns_401(temp_db, client: TestClient):
    """
    Soft-deleted users must receive generic 401 on login without existence leak.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, deleted_at) VALUES (?, ?, '2026-08-23 00:00:00')",
        ("deleted_student", hashed),
    )
    conn.commit()

    response = client.post(
        "/login", json={"username": "deleted_student", "pin": "1234"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or PIN."
