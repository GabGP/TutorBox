import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from db.database import get_db
from security.validation import UUID_RE

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext(BaseModel):
    user_id: int
    username: str
    role: str
    session_id: str
    must_change_pin: bool


def get_current_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    token = credentials.credentials.strip()

    # Validate canonical UUID shape BEFORE hitting SQLite (junk-in guard).
    if UUID_RE.match(token) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.user_id, u.username, u.role, u.must_change_pin "
            "FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            "WHERE s.id = ? AND s.is_active = 1 AND u.deleted_at IS NULL",
            (token,),
        )
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    return AuthContext(
        user_id=row["user_id"],
        username=row["username"],
        role=row["role"],
        session_id=token,
        must_change_pin=bool(row["must_change_pin"]),
    )


def ensure_no_pending_rotation(ctx: AuthContext) -> AuthContext:
    """
    Blocks privileged/interactive endpoints while a PIN rotation is pending.
    Allowlist: PATCH /users/me/pin, GET /users/me, POST /logout.
    """
    if ctx.must_change_pin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PIN change required.",
        )
    return ctx


def require_roles(*allowed: str):
    """Dependency factory: 403 unless the caller's role is in *allowed*."""

    def checker(
        ctx: Annotated[AuthContext, Depends(get_current_session)],
    ) -> AuthContext:
        ensure_no_pending_rotation(ctx)
        if ctx.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return ctx

    return checker
