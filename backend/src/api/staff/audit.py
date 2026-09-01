"""Staff audit logs read endpoint."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from db.database import get_db
from security import (
    AuthContext,
    require_roles,
)

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_LOG_LIMIT: int = 500

router = APIRouter()


class AuditLogsResponse(BaseModel):
    logs: list[dict[str, Any]]


@router.get(
    "/audit-logs",
    response_model=AuditLogsResponse,
)
def read_audit_logs(
    ctx: Annotated[AuthContext, Depends(require_roles("admin"))],
):
    """
    Read up to 500 audit logs in reverse chronological order. Admin only.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, actor_user_id, action, target_user_id, created_at "
            "FROM audit_logs ORDER BY id DESC LIMIT ?",
            (DEFAULT_AUDIT_LOG_LIMIT,),
        )
        rows = cursor.fetchall()

    logger.info("Audit logs viewed by admin '%s'.", ctx.username)
    return AuditLogsResponse(
        logs=[
            {
                "id": r["id"],
                "actor_user_id": r["actor_user_id"],
                "action": r["action"],
                "target_user_id": r["target_user_id"],
                "created_at": str(r["created_at"]) if r["created_at"] else None,
            }
            for r in rows
        ]
    )
