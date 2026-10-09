"""AuthContext carries the clicker a session was issued to (None for a phone login)."""

import uuid
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.db.device_repository import create_device_session
from core.security.auth_session import AuthContext, get_current_session, token_digest
from tests.conftest import auth_headers, get_user_id

CLICKER_ID = "ESP32-A4CF12"

# Sample FastAPI app that echoes the AuthContext resolved for the caller.
sample_app = FastAPI()


@sample_app.get("/test-device")
def route_device(ctx: Annotated[AuthContext, Depends(get_current_session)]):
    return {"user_id": ctx.user_id, "device_id": ctx.device_id}


def test_a_phone_login_carries_no_device(staff_db, client):
    phone_headers = auth_headers(client, "student1")

    response = TestClient(sample_app).get("/test-device", headers=phone_headers)

    assert response.status_code == 200
    assert response.json()["device_id"] is None


def test_a_clicker_session_carries_the_device_it_was_issued_to(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (CLICKER_ID, student_id),
    )
    token = str(uuid.uuid4())
    create_device_session(conn, token_digest(token), student_id, CLICKER_ID)
    conn.commit()

    response = TestClient(sample_app).get(
        "/test-device", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": student_id, "device_id": CLICKER_ID}
