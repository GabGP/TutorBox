"""A clicker's session carries its device, and only get_voter_session accepts it."""

import sqlite3
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.db.device_repository import create_device_session
from core.security.auth_session import (
    CLICKER_SCOPE_DETAIL,
    AuthContext,
    get_current_session,
    get_voter_session,
    require_roles,
    token_digest,
)
from tests.conftest import auth_headers, get_user_id

CLICKER_ID = "ESP32-A4CF12"

# Sample FastAPI app with one route per way an endpoint can ask for the caller.
sample_app = FastAPI()


@sample_app.get("/voter")
def route_voter(ctx: Annotated[AuthContext, Depends(get_voter_session)]):
    return {"user_id": ctx.user_id, "device_id": ctx.device_id}


@sample_app.get("/person")
def route_person(ctx: Annotated[AuthContext, Depends(get_current_session)]):
    return {"user_id": ctx.user_id, "device_id": ctx.device_id}


@sample_app.get("/student")
def route_student(ctx: Annotated[AuthContext, Depends(require_roles("student"))]):
    return {"user_id": ctx.user_id, "device_id": ctx.device_id}


def clicker_headers(conn: sqlite3.Connection, student_id: int) -> dict[str, str]:
    """Registers the clicker for the student and stores a session issued to it."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (CLICKER_ID, student_id),
    )
    token = str(uuid.uuid4())
    create_device_session(conn, token_digest(token), student_id, CLICKER_ID)
    conn.commit()
    return {"Authorization": f"Bearer {token}"}


def test_a_phone_login_carries_no_device(staff_db, client):
    phone_headers = auth_headers(client, "student1")

    response = TestClient(sample_app).get("/voter", headers=phone_headers)

    assert response.status_code == 200
    assert response.json()["device_id"] is None


def test_a_phone_login_is_accepted_on_every_kind_of_route(staff_db, client):
    phone_headers = auth_headers(client, "student1")
    sample_client = TestClient(sample_app)

    statuses = [
        sample_client.get(path, headers=phone_headers).status_code
        for path in ("/voter", "/person", "/student")
    ]

    assert statuses == [200, 200, 200]


def test_a_clicker_session_carries_the_device_it_was_issued_to(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    headers = clicker_headers(conn, student_id)

    response = TestClient(sample_app).get("/voter", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"user_id": student_id, "device_id": CLICKER_ID}


def test_a_clicker_session_is_refused_where_a_persons_login_is_asked_for(staff_db):
    _, conn = staff_db
    headers = clicker_headers(conn, get_user_id(conn, "student1"))

    response = TestClient(sample_app).get("/person", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == CLICKER_SCOPE_DETAIL


def test_a_clicker_session_is_refused_on_a_route_open_to_its_students_role(staff_db):
    _, conn = staff_db
    headers = clicker_headers(conn, get_user_id(conn, "student1"))

    response = TestClient(sample_app).get("/student", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == CLICKER_SCOPE_DETAIL


def test_a_revoked_clicker_session_gets_401_not_the_scope_refusal(staff_db):
    _, conn = staff_db
    headers = clicker_headers(conn, get_user_id(conn, "student1"))
    conn.execute("UPDATE sessions SET is_active = 0 WHERE device_id = ?", (CLICKER_ID,))
    conn.commit()

    response = TestClient(sample_app).get("/person", headers=headers)

    assert response.status_code == 401
