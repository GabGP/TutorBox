import logging
import secrets
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import get_db
from security import (
    AuthContext,
    UsernameField,
    hash_pin,
    require_roles,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class DeleteUserResponse(BaseModel):
    detail: str = "Account deleted."


class RecoverUserRequest(BaseModel):
    username: UsernameField


class RecoverUserResponse(BaseModel):
    username: str
    temporary_pin: str
    detail: str = "Account recovered. User must set a new PIN on next login."


def _soft_delete_user(
    conn: sqlite3.Connection, target_id: int, target_role: str
) -> None:
    cursor = conn.cursor()

    # Last-admin guard: the appliance must never lose its final administrator.
    if target_role == "admin":
        cursor.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND deleted_at IS NULL"
        )
        if cursor.fetchone()["n"] <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete the last remaining admin account.",
            )

    anon_username = f"deleted_user_{target_id}_{secrets.token_hex(4)}"
    unusable_hash = hash_pin(secrets.token_hex(16))
    cursor.execute(
        "UPDATE users SET former_username = username, username = ?, hashed_pin = ?, "
        "deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (anon_username, unusable_hash, target_id),
    )
    cursor.execute(
        "UPDATE sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1",
        (target_id,),
    )


@router.delete(
    "/users/{user_id}",
    response_model=DeleteUserResponse,
    status_code=status.HTTP_200_OK,
)
def delete_user(
    user_id: int,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role FROM users WHERE id = ? AND deleted_at IS NULL",
            (user_id,),
        )
        target = cursor.fetchone()
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )
        if ctx.role == "teacher" and target["role"] == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins may delete admin accounts.",
            )

        _soft_delete_user(conn, user_id, target["role"])
        conn.commit()

    logger.info("User id %d soft-deleted by '%s'.", user_id, ctx.username)
    return DeleteUserResponse()


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
    temp_pin = f"{secrets.randbelow(10**6):06d}"
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
        conn.commit()

    logger.info(
        "Account recovered: user id %d by '%s'.", user_id, ctx.username
    )  # NEVER log temp_pin
    return RecoverUserResponse(
        username=payload.username,
        temporary_pin=temp_pin,
    )
