from fastapi.testclient import TestClient

from src.security.auth import hash_pin


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
