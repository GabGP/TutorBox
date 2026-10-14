"""First-contact enrollment of a clicker: trust on first use.

A clicker makes its own secret and sends it with its first login. If the server has no
secret for that device yet, it keeps the digest of the secret it received. Staff never
issue a secret. The fleet holds at most MAX_DEVICES clickers, so an unknown id past the
cap is not enrolled.
"""

import logging
import sqlite3

from core.db.audit import record_audit
from core.db.device_repository import (
    count_devices,
    enroll_or_claim_device,
    get_device_credentials,
)

logger = logging.getLogger(__name__)

# The most clickers the fleet can hold. Past it, an unknown id is refused.
MAX_DEVICES: int = 100


def enroll_if_new(conn: sqlite3.Connection, device_id: str, secret_digest: str) -> None:
    """Keeps secret_digest as the device's secret when the device has none yet.

    Does nothing when the device already has a secret, and does nothing when the id is
    unknown and the fleet is full. A device added by hand with no secret is claimed.
    The commit happens here, not in the caller: a login that is refused next (403 for
    an unassigned clicker) would otherwise roll the enrollment back.
    """
    credentials = get_device_credentials(conn, device_id)
    if credentials is not None and credentials.secret_hash is not None:
        return
    if credentials is None and count_devices(conn) >= MAX_DEVICES:
        logger.warning("Refused to enroll device '%s': the fleet is full.", device_id)
        return
    if enroll_or_claim_device(conn, device_id, secret_digest):
        record_audit(conn, actor_user_id=None, action="device_enrolled")
        conn.commit()
        logger.info("Device '%s' enrolled.", device_id)
