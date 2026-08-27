import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import get_db
from security import (
    AuthContext,
    PinField,
    UsernameField,
    check_rate_limit,
    ensure_no_pending_rotation,
    get_current_session,
    hash_pin,
    login_rate_limiter,
    verify_pin,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ChangeUsernameRequest(BaseModel):
    current_pin: PinField
    new_username: UsernameField


class ChangePinRequest(BaseModel):
    current_pin: PinField
    new_pin: PinField


class CredentialChangeResponse(BaseModel):
    detail: str = "Credentials updated. Please sign in again."


def _change_credential(
    ctx: AuthContext,
    payload: ChangeUsernameRequest | ChangePinRequest,
    *,
    kind: str,
) -> CredentialChangeResponse:
    logger.info("Credential change (%s) for user '%s'.", kind, ctx.username)

    check_rate_limit(ctx.username)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, hashed_pin FROM users WHERE id = ? AND deleted_at IS NULL",
            (ctx.user_id,),
        )
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session.",
            )

        # 1) Anti-oracle check ordering: verify current PIN FIRST
        if not verify_pin(payload.current_pin, user["hashed_pin"]):
            login_rate_limiter.record_failure(ctx.username)
            logger.warning(
                "Credential change failed (bad current PIN): %s", ctx.username
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current PIN.",
            )
        login_rate_limiter.record_success(ctx.username)

        # 2) Compare new against current only AFTER successful PIN verification
        if kind == "pin":
            assert isinstance(payload, ChangePinRequest)
            if payload.new_pin == payload.current_pin:
                raise HTTPException(
                    status_code=422,
                    detail="New PIN must differ from current PIN.",
                )
            cursor.execute(
                "UPDATE users SET hashed_pin = ?, must_change_pin = 0 WHERE id = ?",
                (hash_pin(payload.new_pin), ctx.user_id),
            )
        else:
            assert isinstance(payload, ChangeUsernameRequest)
            if payload.new_username == ctx.username:
                raise HTTPException(
                    status_code=422,
                    detail="New username must differ from current username.",
                )
            try:
                cursor.execute(
                    "UPDATE users SET username = ? WHERE id = ?",
                    (payload.new_username, ctx.user_id),
                )
            except sqlite3.IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken.",
                )

        # 3) Deactivate ONLY the caller's active session
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE id = ? AND is_active = 1",
            (ctx.session_id,),
        )
        conn.commit()

    logger.info("Credential change (%s) successful for user.", kind)
    return CredentialChangeResponse()


@router.patch("/users/me/username", response_model=CredentialChangeResponse)
def change_username(
    payload: ChangeUsernameRequest,
    ctx: Annotated[AuthContext, Depends(ensure_no_pending_rotation)],
):
    """
    Update username. Requires current PIN verification. Invalidates caller's session.
    """
    return _change_credential(ctx, payload, kind="username")


@router.patch("/users/me/pin", response_model=CredentialChangeResponse)
def change_pin(
    payload: ChangePinRequest,
    ctx: Annotated[AuthContext, Depends(get_current_session)],
):
    """
    Update PIN. Requires current PIN verification. Clears must_change_pin flag.
    Permitted during pending rotation (allowlist). Invalidates caller's session.
    """
    return _change_credential(ctx, payload, kind="pin")
