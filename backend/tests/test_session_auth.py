import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from src.db.database import get_db_connection
from src.security.auth import hash_pin
from src.security.session import (
    AuthContext,
    ensure_no_pending_rotation,
    get_current_session,
    require_roles,
)

# Sample FastAPI app to test session dependencies in isolation
sample_app = FastAPI()


@sample_app.get("/test-session")
def route_session(ctx: Annotated[AuthContext, Depends(get_current_session)]):
    return {
        "user_id": ctx.user_id,
        "username": ctx.username,
        "role": ctx.role,
        "session_id": ctx.session_id,
        "must_change_pin": ctx.must_change_pin,
    }


@sample_app.get("/test-teacher-only")
def route_teacher_only(
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    return {"status": "ok", "user": ctx.username}


@sample_app.get("/test-admin-only")
def route_admin_only(
    ctx: Annotated[AuthContext, Depends(require_roles("admin"))],
):
    return {"status": "ok", "user": ctx.username}


@sample_app.get("/test-no-rotation")
def route_no_rotation(
    ctx: Annotated[AuthContext, Depends(get_current_session)],
):
    ensure_no_pending_rotation(ctx)
    return {"status": "ok"}


def _seed_user_and_session(
    db_path: str,
    username: str,
    role: str = "student",
    is_active: int = 1,
    deleted: bool = False,
    must_change_pin: int = 0,
) -> tuple[int, str]:
    """Helper to seed a user and return (user_id, session_id)."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        hashed = hash_pin("1234")
        deleted_at = "2026-08-23 00:00:00" if deleted else None
        cursor.execute(
            "INSERT INTO users (username, hashed_pin, role, deleted_at, must_change_pin) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, hashed, role, deleted_at, must_change_pin),
        )
        user_id = cursor.lastrowid
        assert user_id is not None
        session_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO sessions (id, user_id, is_active) VALUES (?, ?, ?)",
            (session_id, user_id, is_active),
        )
        conn.commit()
        return user_id, session_id
    finally:
        conn.close()


def test_missing_authorization_header(temp_db):
    client = TestClient(sample_app)
    response = client.get("/test-session")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing or malformed" in response.json()["detail"]


def test_malformed_authorization_header(temp_db):
    client = TestClient(sample_app)
    # Basic scheme instead of Bearer
    response = client.get(
        "/test-session", headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing or malformed" in response.json()["detail"]


def test_invalid_uuid_token_format(temp_db):
    client = TestClient(sample_app)
    # Non-UUID token format (junk in guard)
    response = client.get(
        "/test-session", headers={"Authorization": "Bearer not-a-uuid-token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid session token."


def test_nonexistent_session_token(temp_db):
    client = TestClient(sample_app)
    fake_token = str(uuid.uuid4())
    response = client.get(
        "/test-session", headers={"Authorization": f"Bearer {fake_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired session."


def test_inactive_session_token(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, session_id = _seed_user_and_session(db_path, "inactive_user", is_active=0)
    response = client.get(
        "/test-session", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired session."


def test_soft_deleted_user_session_rejected(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, session_id = _seed_user_and_session(db_path, "deleted_user", deleted=True)
    response = client.get(
        "/test-session", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired session."


def test_valid_active_session_resolves_context(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    user_id, session_id = _seed_user_and_session(
        db_path, "student_valid", role="student", must_change_pin=0
    )
    response = client.get(
        "/test-session", headers={"Authorization": f"Bearer {session_id}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == user_id
    assert data["username"] == "student_valid"
    assert data["role"] == "student"
    assert data["session_id"] == session_id
    assert data["must_change_pin"] is False


def test_require_roles_allows_matching_role(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, teacher_token = _seed_user_and_session(db_path, "teacher1", role="teacher")
    _, admin_token = _seed_user_and_session(db_path, "admin1", role="admin")

    # Teacher accesses teacher-only route
    res_t = client.get(
        "/test-teacher-only",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_t.status_code == status.HTTP_200_OK

    # Admin accesses teacher-only route (since admin is in allowed roles)
    res_a = client.get(
        "/test-teacher-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_a.status_code == status.HTTP_200_OK


def test_require_roles_rejects_insufficient_role(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, student_token = _seed_user_and_session(db_path, "student_user", role="student")
    _, teacher_token = _seed_user_and_session(db_path, "teacher_user", role="teacher")

    # Student cannot access teacher/admin route
    res = client.get(
        "/test-teacher-only",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json()["detail"] == "Insufficient permissions."

    # Teacher cannot access admin-only route
    res_admin = client.get(
        "/test-admin-only",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_admin.status_code == status.HTTP_403_FORBIDDEN
    assert res_admin.json()["detail"] == "Insufficient permissions."


def test_ensure_no_pending_rotation_enforces_gate(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, pending_token = _seed_user_and_session(
        db_path, "must_rotate_user", must_change_pin=1
    )
    _, clean_token = _seed_user_and_session(db_path, "clean_user", must_change_pin=0)

    # Clean user passes
    res_clean = client.get(
        "/test-no-rotation",
        headers={"Authorization": f"Bearer {clean_token}"},
    )
    assert res_clean.status_code == status.HTTP_200_OK

    # User with must_change_pin=1 is blocked with 403
    res_pending = client.get(
        "/test-no-rotation",
        headers={"Authorization": f"Bearer {pending_token}"},
    )
    assert res_pending.status_code == status.HTTP_403_FORBIDDEN
    assert res_pending.json()["detail"] == "PIN change required."


def test_require_roles_blocks_user_with_pending_rotation(temp_db):
    db_path, _ = temp_db
    client = TestClient(sample_app)
    _, teacher_pending = _seed_user_and_session(
        db_path, "teacher_pending", role="teacher", must_change_pin=1
    )

    res = client.get(
        "/test-teacher-only",
        headers={"Authorization": f"Bearer {teacher_pending}"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json()["detail"] == "PIN change required."
