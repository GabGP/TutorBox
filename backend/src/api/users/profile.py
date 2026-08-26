import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from security.session import AuthContext, get_current_session

logger = logging.getLogger(__name__)

router = APIRouter()


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    role: str
    must_change_pin: bool


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
