import logging

import bcrypt

logger = logging.getLogger(__name__)


def hash_pin(pin: str) -> str:
    """
    Hashes a plain-text numeric PIN using bcrypt with salt generation.
    """
    logger.info("Hashing user PIN for secure storage.")
    pin_bytes = pin.encode("utf-8")
    salt = bcrypt.gensalt()
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
