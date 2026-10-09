import hashlib
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core.db.database import get_db
from core.security.validation import UUID_RE

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

# A login lasts one school day: a token copied from a shared tablet stops working
# by the next morning. ponytail: fixed length, make it a SecurityConfig setting
# if a school needs another one.
SESSION_TTL_HOURS = 12


def token_digest(token: str) -> str:
    """What the database keeps for a bearer token: its SHA-256, never the token.

    Tokens are random UUIDs (122 bits), so a fast hash suffices: a digest read
    from the database cannot be turned back into a working token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


class AuthContext(BaseModel):
    user_id: int
    username: str
    role: str
    session_id: str  # sessions.id, the token's digest: safe to store, unlike the token
    must_change_pin: bool
    # The clicker this session was issued to; None for a login from a phone or browser.
    device_id: str | None = None


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

    session_id = token_digest(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.user_id, s.device_id, u.username, u.role, u.must_change_pin "
            "FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            "WHERE s.id = ? AND s.is_active = 1 AND u.deleted_at IS NULL "
            "AND s.created_at > datetime('now', ?)",
            (session_id, f"-{SESSION_TTL_HOURS} hours"),
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
        session_id=session_id,
        must_change_pin=bool(row["must_change_pin"]),
        device_id=row["device_id"],
    )


def ensure_no_pending_rotation(
    ctx: Annotated[AuthContext, Depends(get_current_session)],
) -> AuthContext:
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
        ctx: Annotated[AuthContext, Depends(ensure_no_pending_rotation)],
    ) -> AuthContext:
        if ctx.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return ctx

    return checker
