"""Staff user role change endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.staff.guards import ensure_managers_remain
from core.db.audit import record_audit
from core.db.database import get_db
from core.security import AuthContext, RoleField, require_roles

logger = logging.getLogger(__name__)

router = APIRouter()


class ChangeRoleRequest(BaseModel):
    role: RoleField


class ChangeRoleResponse(BaseModel):
    username: str
    role: str


@router.patch(
    "/users/{user_id}/role",
    response_model=ChangeRoleResponse,
    status_code=status.HTTP_200_OK,
)
def change_user_role(
    user_id: int,
    payload: ChangeRoleRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """
    Changes a user's role. Teachers may move users between student and
    teacher; only admins may assign or touch admin accounts. Demoting the
    last remaining admin is rejected.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role FROM users WHERE id = ? AND deleted_at IS NULL",
            (user_id,),
        )
        target = cursor.fetchone()
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if ctx.role == "teacher" and (
            target["role"] == "admin" or payload.role == "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins may assign or modify admin accounts.",
            )

        if target["role"] == "admin" and payload.role != "admin":
            cursor.execute(
                "SELECT COUNT(*) AS n FROM users "
                "WHERE role = 'admin' AND deleted_at IS NULL"
            )
            if cursor.fetchone()["n"] <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot demote the last remaining admin account.",
                )

        if target["role"] == payload.role:
            return ChangeRoleResponse(username=target["username"], role=target["role"])

        # Last-teacher guard: the classroom must keep someone able to teach.
        if target["role"] == "teacher" and payload.role != "teacher":
            cursor.execute(
                "SELECT COUNT(*) AS n FROM users "
                "WHERE role = 'teacher' AND deleted_at IS NULL"
            )
            if cursor.fetchone()["n"] <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot demote the last remaining teacher account.",
                )

        # Manager floor: demoting to student must not lock out the appliance.
        if payload.role == "student":
            ensure_managers_remain(conn, target["role"], verb="demote")

        cursor.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (payload.role, user_id),
        )
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="role_changed",
            target_user_id=user_id,
        )
        conn.commit()

    logger.info(
        "Role changed: user id %d to '%s' by '%s'.",
        user_id,
        payload.role,
        ctx.username,
    )
    return ChangeRoleResponse(username=target["username"], role=payload.role)
