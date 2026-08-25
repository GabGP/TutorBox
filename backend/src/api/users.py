import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from db.database import get_db
from security.auth import hash_pin
from security.rate_limit import signup_rate_limiter
from security.session import AuthContext, get_current_session
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
