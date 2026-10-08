import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from api.auth.schemas import LoginRequest, LoginResponse
from core.db.database import get_db
from core.security import (
    check_rate_limit,
    login_key,
    login_rate_limiter,
    token_digest,
    verify_pin,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, http: Request):
    """
    Authenticates a student by username and numeric PIN.

    Failures lock out this name on this device only (login_key).
    """
    logger.info("Attempting login for user: %s", request.username)

    limit_key = login_key(request.username, http)
    check_rate_limit(limit_key)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, hashed_pin, must_change_pin "
            "FROM users WHERE username = ? AND deleted_at IS NULL",
            (request.username,),
        )
        user = cursor.fetchone()

        if not user:
            login_rate_limiter.record_failure(limit_key)
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
            login_rate_limiter.record_failure(limit_key)
            logger.warning("Login failed: Invalid PIN for user '%s'.", request.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or PIN.",
            )

        login_rate_limiter.record_success(limit_key)

        # Create the session: the client gets the token, the database its digest
        token = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO sessions (id, user_id, is_active) VALUES (?, ?, 1)",
            (token_digest(token), user_id),
        )
        conn.commit()

    logger.info("Login successful for user '%s'.", username)
    return LoginResponse(
        session_id=token,
        username=username,
        must_change_pin=bool(user["must_change_pin"]),
    )
