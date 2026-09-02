import logging
import secrets

import bcrypt

from config import DEFAULT_BCRYPT_ROUNDS, get_settings
from security.validation import DEFAULT_TEMP_PIN_LENGTH

logger = logging.getLogger(__name__)

__all__ = [
    "DEFAULT_BCRYPT_ROUNDS",
    "generate_temporary_pin",
    "get_bcrypt_rounds",
    "hash_pin",
    "verify_pin",
]


def get_bcrypt_rounds() -> int:
    """Returns configured bcrypt rounds, falling back to production constant (12)."""
    return get_settings(reload=True).security.bcrypt_rounds


def generate_temporary_pin(length: int = DEFAULT_TEMP_PIN_LENGTH) -> str:
    """Generates a cryptographically secure random numeric temporary PIN."""
    return f"{secrets.randbelow(10**length):0{length}d}"


def hash_pin(pin: str, rounds: int | None = None) -> str:
    """
    Hashes a plain-text numeric PIN using bcrypt with salt generation.
    """
    logger.info("Hashing user PIN for secure storage.")
    work_factor = rounds if rounds is not None else get_bcrypt_rounds()
    pin_bytes = pin.encode("utf-8")
    salt = bcrypt.gensalt(rounds=work_factor)
    hashed = bcrypt.hashpw(pin_bytes, salt)
    return hashed.decode("utf-8")


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """
    Verifies a plain-text PIN against a stored bcrypt hash.
    """
    try:
        is_valid = bcrypt.checkpw(plain_pin.encode("utf-8"), hashed_pin.encode("utf-8"))
        if is_valid:
            logger.info("PIN verification succeeded.")
        else:
            logger.warning("PIN verification failed: Invalid PIN provided.")
        return is_valid
    except (ValueError, TypeError) as e:
        logger.error("Error during PIN verification: %s", type(e).__name__)
        return False
