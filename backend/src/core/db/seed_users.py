"""Bootstrap teacher account so a fresh appliance can host quiz sessions out of the box."""

import logging

from core.config import get_settings
from core.db.database import get_db_connection
from core.security.auth import hash_pin

logger = logging.getLogger(__name__)


def seed_teacher(db_path: str) -> bool:
    """Creates the configured teacher account if no user has that username.

    Returns True when a row was inserted. Idempotent; disabled when either
    SEED_TEACHER_USERNAME or SEED_TEACHER_PIN is empty.
    """
    cfg = get_settings(reload=True).security
    username, pin = cfg.seed_teacher_username, cfg.seed_teacher_pin
    if not username or not pin:
        logger.info("Teacher seeding disabled (SEED_TEACHER_* is empty).")
        return False

    conn = get_db_connection(db_path)
    try:
        with conn:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if exists:
                return False
            conn.execute(
                "INSERT INTO users (username, hashed_pin, role) "
                "VALUES (?, ?, 'teacher')",
                (username, hash_pin(pin)),
            )
        logger.info("Seeded bootstrap teacher account '%s'.", username)
        return True
    finally:
        conn.close()
