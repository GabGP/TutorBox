from fastapi.testclient import TestClient

from src.db.database import get_db_connection
from src.security.auth import hash_pin


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


def test_get_me_success(seeded_db, client: TestClient):
    """
    GET /users/me returns authenticated caller profile.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_res.status_code == 200
    token = login_res.json()["session_id"]

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "student1"
    assert data["role"] == "student"
    assert data["must_change_pin"] is False
    assert isinstance(data["user_id"], int)


def test_get_me_unauthenticated(client: TestClient):
    """
    GET /users/me without Bearer header returns 401.
    """
    response = client.get("/users/me")
    assert response.status_code == 401


def test_get_me_permitted_during_pending_rotation(temp_db, client: TestClient):
    """
    GET /users/me is on the forced-rotation allowlist and returns 200 with must_change_pin=True.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, must_change_pin) VALUES (?, ?, 1)",
        ("must_rotate", hashed),
    )
    conn.commit()

    login_res = client.post("/login", json={"username": "must_rotate", "pin": "1234"})
    assert login_res.status_code == 200
    token = login_res.json()["session_id"]

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "must_rotate"
    assert data["must_change_pin"] is True
