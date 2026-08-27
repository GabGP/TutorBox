from src.security.auth import hash_pin, verify_pin


def test_hash_pin_generates_bcrypt_hash():
    """
    Test that hash_pin produces a valid bcrypt hash starting with $2b$.
    """
    pin = "1234"
    hashed = hash_pin(pin)
    assert hashed != pin
    assert hashed.startswith(("$2b$", "$2a$"))


def test_hash_pin_generates_unique_salts():
    """
    Test that hashing the same PIN twice yields different hash strings due to salt.
    """
    pin = "1234"
    hash1 = hash_pin(pin)
    hash2 = hash_pin(pin)
    assert hash1 != hash2
    assert verify_pin(pin, hash1) is True
    assert verify_pin(pin, hash2) is True


def test_verify_pin_success():
    """
    Test verify_pin returns True for valid PIN and hash.
    """
    pin = "5678"
    hashed = hash_pin(pin)
    assert verify_pin(pin, hashed) is True


def test_verify_pin_failure():
    """
    Test verify_pin returns False for incorrect PIN.
    """
    pin = "5678"
    hashed = hash_pin(pin)
    assert verify_pin("0000", hashed) is False


def test_verify_pin_invalid_hash_format():
    """
    Test verify_pin handles invalid hash string format gracefully without crashing.
    """
    assert verify_pin("1234", "not_a_valid_bcrypt_hash") is False
