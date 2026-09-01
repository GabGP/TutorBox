from fastapi.testclient import TestClient

from src.db.database import get_db_connection


def test_logout_success_deactivates_session(seeded_db, client: TestClient):
    """
    POST /logout must deactivate the active session in SQLite.
    """
    db_path, _ = seeded_db
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    assert login_res.status_code == 200
    session_id = login_res.json()["session_id"]

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["detail"] == "Logged out."

    # Verify session is deactivated in DB
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row["is_active"] == 0
    conn.close()


def test_logout_idempotent_and_subsequent_request_fails(seeded_db, client: TestClient):
    """
    Calling logout deactivates session; a second attempt with that dead token
    fails at the Bearer dependency (401).
    """
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    session_id = login_res.json()["session_id"]

    # First logout succeeds
    res1 = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert res1.status_code == 200

    # Second call with the same token fails with 401 because session is no longer active
    res2 = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert res2.status_code == 401


def test_logout_unauthenticated_returns_401(client: TestClient):
    """
    Calling /logout without Bearer header returns 401.
    """
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 401
