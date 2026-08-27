import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.users.credentials import ChangePinRequest, _change_credential
from src.security.auth import hash_pin
from src.security.session import AuthContext


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
