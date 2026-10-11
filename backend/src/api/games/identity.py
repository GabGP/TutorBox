"""Who sent a batch of game events: a logged-in student, or nobody."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.security.auth_session import bearer_scheme, get_current_session

__all__ = ["optional_student_id"]


def optional_student_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> int | None:
    """The logged-in student's id, or None. The games ask for no login."""
    if credentials is None:
        return None
    try:
        context = get_current_session(credentials)
    except HTTPException:
        # An expired login must not block the phone's queue: the events are stored
        # without a student instead of being refused.
        return None
    return context.user_id if context.role == "student" else None
