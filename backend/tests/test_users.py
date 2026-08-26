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


def test_change_pin_success(seeded_db, client: TestClient):
    """
    PATCH /users/me/pin changes PIN, clears must_change_pin, and deactivates caller's session.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_res.status_code == 200
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_pin": "5678"},
    )
    assert res.status_code == 200
    assert res.json()["detail"] == "Credentials updated. Please sign in again."

    # Caller's old session is now inactive
    me_res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401

    # Old PIN rejected
    login_old = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_old.status_code == 401

    # New PIN accepted with must_change_pin = False
    login_new = client.post("/login", json={"username": "student1", "pin": "5678"})
    assert login_new.status_code == 200
    assert login_new.json()["must_change_pin"] is False


def test_change_pin_clears_must_change_pin(temp_db, client: TestClient):
    """
    PATCH /users/me/pin clears must_change_pin flag during forced rotation.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, must_change_pin) VALUES (?, ?, 1)",
        ("rotate_user", hashed),
    )
    conn.commit()

    login_res = client.post("/login", json={"username": "rotate_user", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_pin": "9876"},
    )
    assert res.status_code == 200

    login_new = client.post("/login", json={"username": "rotate_user", "pin": "9876"})
    assert login_new.status_code == 200
    assert login_new.json()["must_change_pin"] is False


def test_anti_oracle_pin_change_order(seeded_db, client: TestClient):
    """
    Anti-oracle check ordering: wrong current_pin with new_pin == current_pin
    MUST return 401 Unauthorized, never 422.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "9999", "new_pin": "9999"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid current PIN."


def test_change_pin_same_pin_returns_422(seeded_db, client: TestClient):
    """
    Correct current_pin but new_pin == current_pin returns 422 Unprocessable Entity.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_pin": "1234"},
    )
    assert res.status_code == 422
    assert "New PIN must differ" in res.json()["detail"]


def test_change_pin_wrong_current_pin_returns_401(seeded_db, client: TestClient):
    """
    Wrong current_pin on PIN change returns 401.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "0000", "new_pin": "5678"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid current PIN."


def test_change_username_success(seeded_db, client: TestClient):
    """
    PATCH /users/me/username updates username, deactivates session, and frees old username.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "renamed_student"},
    )
    assert res.status_code == 200
    assert res.json()["detail"] == "Credentials updated. Please sign in again."

    # Caller session is now inactive
    me_res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401

    # Login with old username fails
    login_old = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_old.status_code == 401

    # Login with new username succeeds
    login_new = client.post(
        "/login", json={"username": "renamed_student", "pin": "1234"}
    )
    assert login_new.status_code == 200

    # Old username is immediately freed for self-signup reuse
    signup_reuse = client.post("/signup", json={"username": "student1", "pin": "4321"})
    assert signup_reuse.status_code == 201


def test_change_username_same_name_returns_422(seeded_db, client: TestClient):
    """
    PATCH /users/me/username with same username returns 422 Unprocessable Entity.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "student1"},
    )
    assert res.status_code == 422
    assert "New username must differ" in res.json()["detail"]


def test_change_username_duplicate_returns_409(staff_db, client: TestClient):
    """
    PATCH /users/me/username with an already taken username returns 409 Conflict.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "student2"},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Username already taken."


def test_change_username_blocked_during_pending_rotation(temp_db, client: TestClient):
    """
    PATCH /users/me/username is blocked (403 Forbidden) when user must rotate PIN.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, must_change_pin) VALUES (?, ?, 1)",
        ("must_rotate_user", hashed),
    )
    conn.commit()

    login_res = client.post(
        "/login", json={"username": "must_rotate_user", "pin": "1234"}
    )
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "fresh_user"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_anti_oracle_username_change_order(seeded_db, client: TestClient):
    """
    Anti-oracle check ordering on username change: wrong current PIN with same username
    MUST return 401 Unauthorized, never 422.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "9999", "new_username": "student1"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid current PIN."


def test_credential_change_rate_limiting(seeded_db, client: TestClient):
    """
    Repeated bad current PIN on credential change increments login rate limiter and triggers 429.
    """
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    token = login_res.json()["session_id"]

    # 4 bad attempts return 401
    for _ in range(4):
        res = client.patch(
            "/users/me/pin",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_pin": "0000", "new_pin": "5678"},
        )
        assert res.status_code == 401

    # 5th bad attempt triggers lockout
    res_5th = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "0000", "new_pin": "5678"},
    )
    assert res_5th.status_code == 401

    # 6th attempt is blocked by rate limiter with 429
    res_6th = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "0000", "new_pin": "5678"},
    )
    assert res_6th.status_code == 429
    assert "Too many failed login attempts" in res_6th.json()["detail"]

    # /login is also locked out uniformly
    login_locked = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_locked.status_code == 429


def test_change_credential_user_deleted_returns_401(temp_db, client: TestClient):
    """
    If a user is soft-deleted after session creation, credential change returns 401 Invalid session.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin) VALUES (?, ?)",
        ("temp_user", hashed),
    )
    conn.commit()

    login_res = client.post("/login", json={"username": "temp_user", "pin": "1234"})
    token = login_res.json()["session_id"]

    # Soft-delete the user directly in SQLite
    cursor.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE username = 'temp_user'"
    )
    conn.commit()

    res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_pin": "5678"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid or expired session."


def test_change_credential_missing_user(temp_db):
    """
    Defensive check: if caller's user record is missing in _change_credential, raise 401.
    """
    import pytest
    from fastapi import HTTPException

    from src.api.users import ChangePinRequest, _change_credential
    from src.security.session import AuthContext

    ctx = AuthContext(
        user_id=9999,
        username="ghost",
        role="student",
        session_id="00000000-0000-0000-0000-000000000000",
        must_change_pin=False,
    )
    with pytest.raises(HTTPException) as exc:
        _change_credential(
            ctx,
            ChangePinRequest(current_pin="1234", new_pin="5678"),
            kind="pin",
        )
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid session."
