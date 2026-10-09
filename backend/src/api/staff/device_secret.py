import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.staff.schemas import DeviceSecretResponse
from core.db.audit import record_audit
from core.db.database import get_db
from core.db.device_repository import (
    get_device_credentials,
    revoke_device_sessions,
    store_device_secret,
)
from core.security import (
    AuthContext,
    require_roles,
    token_digest,
)

logger = logging.getLogger(__name__)
# 16 random bytes render as 32 lowercase hex characters.
DEVICE_SECRET_RANDOM_BYTES: int = 16
router = APIRouter()


@router.post("/devices/{device_id}/secret", response_model=DeviceSecretResponse)
def issue_device_secret(
    device_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Issues a new clicker secret; revokes the tokens issued under the old one."""
    with get_db() as conn:
        device = get_device_credentials(conn, device_id)
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
            )

        secret = secrets.token_hex(DEVICE_SECRET_RANDOM_BYTES)
        store_device_secret(conn, device_id, token_digest(secret))
        revoke_device_sessions(conn, device_id)
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="device_secret_issued",
            target_user_id=device.assigned_user_id,
        )
        conn.commit()

    logger.info("Issued a new secret for clicker %s.", device_id)
    return DeviceSecretResponse(device_id=device_id, secret=secret)
