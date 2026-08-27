import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from db.database import get_db
from security.session import AuthContext, get_current_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/logout")
def logout(ctx: Annotated[AuthContext, Depends(get_current_session)]):
    """
    Deactivates the caller's current session.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE id = ? AND is_active = 1",
            (ctx.session_id,),
        )
        conn.commit()

    logger.info("User '%s' logged out.", ctx.username)
    return {"detail": "Logged out."}
