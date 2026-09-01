from fastapi.testclient import TestClient

from src.security.auth import hash_pin


def test_change_username_success(seeded_db, client: TestClient):
    """
    PATCH /users/me/username updates username, deactivates session, and frees old username.
    """
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["session_id"]

    res = client.patch(
        "/api/v1/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "renamed_student"},
    )
    assert res.status_code == 200
    assert res.json()["detail"] == "Credentials updated. Please sign in again."

    # Caller session is now inactive
    me_res = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 401

    # Login with old username fails
    login_old = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    assert login_old.status_code == 401

    # Login with new username succeeds
    login_new = client.post(
        "/api/v1/auth/login", json={"username": "renamed_student", "pin": "1234"}
    )
    assert login_new.status_code == 200

    # Old username is immediately freed for self-signup reuse
    signup_reuse = client.post(
        "/api/v1/users/signup", json={"username": "student1", "pin": "4321"}
    )
    assert signup_reuse.status_code == 201


def test_change_username_same_name_returns_422(seeded_db, client: TestClient):
    """
    PATCH /users/me/username with same username returns 422 Unprocessable Entity.
    """
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    token = login_res.json()["session_id"]

    res = client.patch(
        "/api/v1/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "1234", "new_username": "student1"},
    )
    assert res.status_code == 422
    assert "New username must differ" in res.json()["detail"]


def test_change_username_duplicate_returns_409(staff_db, client: TestClient):
    """
    PATCH /users/me/username with an already taken username returns 409 Conflict.
    """
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    token = login_res.json()["session_id"]

    res = client.patch(
        "/api/v1/users/me/username",
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
        "/api/v1/auth/login", json={"username": "must_rotate_user", "pin": "1234"}
    )
    token = login_res.json()["session_id"]

    res = client.patch(
        "/api/v1/users/me/username",
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
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    token = login_res.json()["session_id"]

    res = client.patch(
        "/api/v1/users/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_pin": "9999", "new_username": "student1"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid current PIN."
