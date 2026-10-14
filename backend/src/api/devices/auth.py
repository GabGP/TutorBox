"""Public clicker login: a device's secret in, a bearer token for its student out.

A clicker holds no PIN. It proves itself with a secret it made itself. The first
secret a device sends is kept (enrollment, see enrollment.py), and every later login
must send that same secret. The login gives an ordinary session for the student the
clicker is assigned to. Its lockout key starts with "device:", so a clicker never
shares a lockout with a username.
"""

import hmac
import logging
import sqlite3
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from api.devices.enrollment import enroll_if_new
from api.devices.schemas import DeviceAuthRequest, DeviceAuthResponse
from core.db.database import get_db
from core.db.device_repository import (
    DeviceCredentials,
    create_device_session,
    get_device_credentials,
    revoke_device_sessions,
)
from core.security import (
    check_rate_limit,
    login_key,
    login_rate_limiter,
    token_digest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

INVALID_DEVICE_CREDENTIALS_DETAIL = "Invalid device credentials."
UNASSIGNED_DEVICE_DETAIL = "Device is not assigned to any student."


def _verify_device_secret(
    conn: sqlite3.Connection, limit_key: str, payload: DeviceAuthRequest
) -> DeviceCredentials:
    """Returns the clicker's credentials when the secret is right, otherwise raises 401.

    A wrong secret and an unknown device are refused alike: same status, same detail,
    same failure recorded. enroll_if_new runs first, so an unknown device is refused
    here only when the fleet is full, and a device with no secret has one by now.
    """
    credentials = get_device_credentials(conn, payload.device_id)
    if (
        credentials is None
        or credentials.secret_hash is None
        or not hmac.compare_digest(
            credentials.secret_hash, token_digest(payload.secret)
        )
    ):
        login_rate_limiter.record_failure(limit_key)
        logger.warning(
            "Device authentication failed for device '%s'.", payload.device_id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_DEVICE_CREDENTIALS_DETAIL,
        )

    login_rate_limiter.record_success(limit_key)
    return credentials


@router.post("/auth", response_model=DeviceAuthResponse)
def authenticate_device(
    payload: DeviceAuthRequest, http: Request
) -> DeviceAuthResponse:
    """
    Trades a clicker's secret for a login session of the student it is assigned to.

    The first secret sent for a device is enrolled (trust on first use). Wrong
    secrets lock out this device on this address (login_key). A device with the
    right secret but no student assigned gets 403 and is not counted as a failure,
    so a clicker waiting for the teacher can retry every 5 seconds.
    """
    limit_key = login_key(f"device:{payload.device_id}", http)
    check_rate_limit(limit_key)

    with get_db() as conn:
        enroll_if_new(conn, payload.device_id, token_digest(payload.secret))
        credentials = _verify_device_secret(conn, limit_key, payload)
        # The id and the username come from the same joined row: both or neither.
        if (
            credentials.assigned_user_id is None
            or credentials.assigned_username is None
        ):
            logger.info("Device '%s' has no student assigned.", payload.device_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=UNASSIGNED_DEVICE_DETAIL,
            )

        # The client gets the token, the database its digest. A clicker has one live
        # token: a new login ends the previous one.
        token = str(uuid.uuid4())
        revoke_device_sessions(conn, payload.device_id)
        create_device_session(
            conn, token_digest(token), credentials.assigned_user_id, payload.device_id
        )
        conn.commit()

    logger.info("Device '%s' authenticated.", payload.device_id)
    return DeviceAuthResponse(
        session_id=token,
        username=credentials.assigned_username,
        device_id=payload.device_id,
    )
