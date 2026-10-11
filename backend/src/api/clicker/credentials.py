"""How a hardware clicker proves who it is, on every request.

Each ESP32 generates a random 128-bit secret on first boot and keeps it in flash. It
sends `X-Clicker-Id` and `X-Clicker-Secret` headers; the appliance keeps only the
secret's SHA-256 (a random secret needs no slow hash, same as session tokens).

The first check-in from an unknown id enrolls it, trust-on-first-use. That is safe
here because enrolling grants nothing: an enrolled clicker votes only after a teacher
assigns it to a student, the same trust decision the BLE design relied on
(docs/architecture/esp32-protocol.md section 5). A phone cannot vote as a clicker
without that clicker's secret.
"""

import hmac
import sqlite3
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, status

from core.db.audit import record_audit
from core.db.clicker_repository import (
    MAX_CLICKERS,
    ClickerRecord,
    count_clickers,
    enroll_or_claim_clicker,
    get_clicker,
)
from core.security import DEVICE_ID_PATTERN, token_digest

__all__ = [
    "SECRET_PATTERN",
    "ClickerCredentials",
    "authenticate_clicker",
    "clicker_credentials",
]

# The firmware sends 32 lowercase hex digits; up to 64 leaves room for a longer secret.
SECRET_PATTERN = r"^[0-9a-f]{32,64}$"


@dataclass(frozen=True)
class ClickerCredentials:
    device_id: str
    secret: str


def clicker_credentials(
    x_clicker_id: Annotated[str, Header(pattern=DEVICE_ID_PATTERN)],
    x_clicker_secret: Annotated[str, Header(pattern=SECRET_PATTERN)],
) -> ClickerCredentials:
    """Reads the clicker headers; a missing or malformed one is a 422."""
    return ClickerCredentials(device_id=x_clicker_id, secret=x_clicker_secret)


def _enroll_if_new(conn: sqlite3.Connection, device_id: str, digest: str) -> None:
    existing = get_clicker(conn, device_id)
    if existing is not None and existing.secret_hash is not None:
        return
    if existing is None and count_clickers(conn) >= MAX_CLICKERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Clicker limit ({MAX_CLICKERS}) reached. Remove unused clickers.",
        )
    if enroll_or_claim_clicker(conn, device_id, digest):
        record_audit(conn, actor_user_id=None, action="device_enrolled")


def authenticate_clicker(
    conn: sqlite3.Connection, creds: ClickerCredentials, *, enroll: bool
) -> ClickerRecord:
    """Returns the clicker's row once its secret matches; 401 otherwise.

    With enroll=True (check-in), an unknown id, or one a teacher registered by hand,
    is enrolled with this secret first. Voting never enrolls.
    """
    digest = token_digest(creds.secret)
    if enroll:
        _enroll_if_new(conn, creds.device_id, digest)
    record = get_clicker(conn, creds.device_id)
    if (
        record is None
        or record.secret_hash is None
        or not hmac.compare_digest(record.secret_hash, digest)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clicker not recognized: unknown id or wrong secret.",
        )
    return record
