import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from db.database import get_db
from security.auth import hash_pin, verify_pin
from security.rate_limit import (
    check_rate_limit,
    login_rate_limiter,
    signup_rate_limiter,
)
from security.session import (
    AuthContext,
    ensure_no_pending_rotation,
    get_current_session,
)
from security.validation import (
    PIN_MAX_LENGTH,
    PIN_MIN_LENGTH,
    PIN_PATTERN,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        examples=["student2"],
    )
    pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
        examples=["1234"],
    )


class SignupResponse(BaseModel):
    username: str
    role: str


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    role: str
    must_change_pin: bool


class ChangeUsernameRequest(BaseModel):
    current_pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
    )
    new_username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
    )


class ChangePinRequest(BaseModel):
    current_pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
    )
    new_pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
    )


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


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(request: SignupRequest):
    """
    Student self-signup. Role is always 'student' with direct activation.
    """
    logger.info("Signup attempt for username: %s", request.username)

    if not signup_rate_limiter.allow():
        logger.warning("Signup rate limit exceeded.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later.",
        )

    hashed = hash_pin(request.pin)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, 'student')",
                (request.username, hashed),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(
            "Signup conflict: Username '%s' already exists.", request.username
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )

    logger.info("User '%s' registered successfully.", request.username)
    return SignupResponse(username=request.username, role="student")


@router.get("/users/me", response_model=UserProfileResponse)
def get_me(ctx: Annotated[AuthContext, Depends(get_current_session)]):
    """
    Returns caller's profile. Permitted during pending rotation (allowlist).
    """
    return UserProfileResponse(
        user_id=ctx.user_id,
        username=ctx.username,
        role=ctx.role,
        must_change_pin=ctx.must_change_pin,
    )


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
