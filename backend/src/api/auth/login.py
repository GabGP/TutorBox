import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db.database import get_db
from security import (
    PinField,
    UsernameField,
    check_rate_limit,
    login_rate_limiter,
    verify_pin,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: UsernameField
    pin: PinField


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
