import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.audit import record_audit
from db.database import get_db
from security import (
    AuthContext,
    UsernameField,
    generate_temporary_pin,
    hash_pin,
    require_roles,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RecoverUserRequest(BaseModel):
    username: UsernameField


class RecoverUserResponse(BaseModel):
    username: str
    temporary_pin: str
    detail: str = "Account recovered. User must set a new PIN on next login."


@router.post(
    "/users/{user_id}/recover",
    response_model=RecoverUserResponse,
    status_code=status.HTTP_200_OK,
)
def recover_user(
    user_id: int,
    payload: RecoverUserRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    temp_pin = generate_temporary_pin()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role FROM users WHERE id = ? AND deleted_at IS NOT NULL",
            (user_id,),
        )
        target = cursor.fetchone()
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deleted user not found."
            )
        # Uniform matrix: teachers recover students/teachers; admins anyone.
        if ctx.role == "teacher" and target["role"] == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins may recover admin accounts.",
            )

        try:
            cursor.execute(
                "UPDATE users SET username = ?, hashed_pin = ?, "
                "deleted_at = NULL, must_change_pin = 1 "
                "WHERE id = ? AND deleted_at IS NOT NULL",
                (payload.username, hash_pin(temp_pin), user_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken. Choose another for this account.",
            )
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="account_recovered",
            target_user_id=user_id,
        )
        conn.commit()

    logger.info(
        "Account recovered: user id %d by '%s'.", user_id, ctx.username
    )  # NEVER log temp_pin
    return RecoverUserResponse(
        username=payload.username,
        temporary_pin=temp_pin,
    )
