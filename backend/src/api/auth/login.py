import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from db.database import get_db
from security.auth import verify_pin
from security.rate_limit import check_rate_limit, login_rate_limiter
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


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        examples=["student1"],
    )
    pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
        examples=["1234"],
    )


class LoginResponse(BaseModel):
    session_id: str
    username: str
    status: str = "authenticated"
    must_change_pin: bool = False


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticates a student by username and numeric PIN.
    """
    logger.info("Attempting login for user: %s", request.username)

    check_rate_limit(request.username)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, hashed_pin, must_change_pin "
            "FROM users WHERE username = ? AND deleted_at IS NULL",
            (request.username,),
        )
        user = cursor.fetchone()

        if not user:
            login_rate_limiter.record_failure(request.username)
            logger.warning("Login failed: User '%s' not found.", request.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or PIN.",
            )

        user_id, username, stored_hashed_pin = (
            user["id"],
            user["username"],
            user["hashed_pin"],
        )

        if not verify_pin(request.pin, stored_hashed_pin):
            login_rate_limiter.record_failure(request.username)
            logger.warning("Login failed: Invalid PIN for user '%s'.", request.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or PIN.",
            )

        login_rate_limiter.record_success(request.username)

        # Create active session
        session_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO sessions (id, user_id, is_active) VALUES (?, ?, 1)",
            (session_id, user_id),
        )
        conn.commit()

    logger.info("Login successful for user '%s'.", username)
    return LoginResponse(
        session_id=session_id,
        username=username,
        must_change_pin=bool(user["must_change_pin"]),
    )
