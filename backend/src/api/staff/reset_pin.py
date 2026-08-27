import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import get_db
from security import (
    AuthContext,
    hash_pin,
    require_roles,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ResetPinResponse(BaseModel):
    username: str
    temporary_pin: str


@router.post(
    "/users/{user_id}/reset-pin",
    response_model=ResetPinResponse,
    status_code=status.HTTP_200_OK,
)
def reset_pin(
    user_id: int,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """
    Teacher-initiated temporary PIN reset.
    Generates a 6-digit temporary PIN, sets must_change_pin=1, and invalidates all active sessions for the target user.
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

        # Uniform matrix: teachers act on students/teachers; admins on anyone.
        if ctx.role == "teacher" and target["role"] == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins may reset admin PINs.",
            )

        temp_pin = f"{secrets.randbelow(10**6):06d}"
        cursor.execute(
            "UPDATE users SET hashed_pin = ?, must_change_pin = 1 WHERE id = ?",
            (hash_pin(temp_pin), user_id),
        )
        # Invalidate all active sessions for the target user
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1",
            (user_id,),
        )
        conn.commit()

    logger.info("PIN reset issued for user id %d.", user_id)  # NEVER log temp_pin
    return ResetPinResponse(username=target["username"], temporary_pin=temp_pin)
