import logging
import sqlite3

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db.database import get_db
from security import (
    PinField,
    UsernameField,
    hash_pin,
    signup_rate_limiter,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SignupRequest(BaseModel):
    username: UsernameField
    pin: PinField


class SignupResponse(BaseModel):
    username: str
    role: str


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
