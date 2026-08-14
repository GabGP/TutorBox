import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.db.database import get_db_connection
from src.security.auth import verify_pin

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["student1"])
    pin: str = Field(..., examples=["1234"])


class LoginResponse(BaseModel):
    session_id: str
    username: str
    status: str = "authenticated"


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticates a student by username and numeric PIN.
    """
    logger.info(f"Attempting login for user: {request.username}")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, hashed_pin FROM users WHERE username = ?",
        (request.username,),
    )
    user = cursor.fetchone()

    if not user:
        logger.warning(f"Login failed: User '{request.username}' not found.")
        conn.close()
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
        logger.warning(f"Login failed: Invalid PIN for user '{request.username}'.")
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or PIN.",
        )

    # Create active session
    session_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sessions (id, user_id, is_active) VALUES (?, ?, 1)",
        (session_id, user_id),
    )
    conn.commit()
    conn.close()

    logger.info(f"Login successful for user '{username}'. Session ID: {session_id}")
    return LoginResponse(session_id=session_id, username=username)
