from fastapi.testclient import TestClient

from src.db.database import get_db_connection


def test_signup_success(temp_db, client: TestClient):
    """
    POST /signup creates an active student account and returns 201 Created.
    """
    db_path, _ = temp_db
    response = client.post("/signup", json={"username": "new_student", "pin": "1234"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_student"
    assert data["role"] == "student"

    # Verify user row in SQLite
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, role, must_change_pin, deleted_at FROM users WHERE username = ?",
        ("new_student",),
    )
    user = cursor.fetchone()
    assert user is not None
    assert user["role"] == "student"
    assert user["must_change_pin"] == 0
    assert user["deleted_at"] is None
    conn.close()


def test_signup_duplicate_username_returns_409(seeded_db, client: TestClient):
    """
    POST /signup with an existing username returns 409 Conflict.
    """
    response = client.post("/signup", json={"username": "student1", "pin": "5678"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."


def test_signup_rate_limiting_triggers_429(temp_db, client: TestClient, monkeypatch):
    """
    Global signup limiter throttles after limit is reached, returning 429.
    """
    import sys

    for mod_name in ("security.rate_limit", "src.security.rate_limit"):
        if mod_name in sys.modules:
            monkeypatch.setattr(
                sys.modules[mod_name].signup_rate_limiter, "allow", lambda: False
            )

    res = client.post("/signup", json={"username": "flood_blocked", "pin": "1234"})
    assert res.status_code == 429
    assert "Too many signup attempts" in res.json()["detail"]


def test_signup_validation_errors(temp_db, client: TestClient):
    """
    POST /signup validates input bounds and formats, returning 422 Unprocessable Entity.
    """
    # Oversized username
    assert (
        client.post("/signup", json={"username": "a" * 33, "pin": "1234"}).status_code
        == 422
    )

    # Undersized username
    assert (
        client.post("/signup", json={"username": "ab", "pin": "1234"}).status_code
        == 422
    )

    # Invalid characters in username
    assert (
        client.post(
            "/signup", json={"username": "user space", "pin": "1234"}
        ).status_code
        == 422
    )

    # Non-numeric PIN
    assert (
        client.post(
            "/signup", json={"username": "valid_user", "pin": "abcd"}
        ).status_code
        == 422
    )

    # Short PIN (<4)
    assert (
        client.post(
            "/signup", json={"username": "valid_user", "pin": "123"}
        ).status_code
        == 422
    )

    # Long PIN (>8)
    assert (
        client.post(
            "/signup", json={"username": "valid_user", "pin": "123456789"}
        ).status_code
        == 422
    )
