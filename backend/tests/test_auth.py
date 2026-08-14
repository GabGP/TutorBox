from fastapi.testclient import TestClient

from src.db.database import get_db_connection
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


def test_login_success(seeded_db, client: TestClient):
    """
    Test successful student login returns 200 OK and session_id.
    """
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["username"] == "student1"
    assert data["status"] == "authenticated"


def test_login_incorrect_pin(seeded_db, client: TestClient):
    """
    Test login with incorrect PIN returns 401 Unauthorized.
    """
    response = client.post("/login", json={"username": "student1", "pin": "9999"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid username or PIN."


def test_login_user_not_found(seeded_db, client: TestClient):
    """
    Test login with non-existent user returns 401 Unauthorized.
    """
    response = client.post("/login", json={"username": "unknown_user", "pin": "1234"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid username or PIN."


def test_login_creates_database_session(seeded_db, client: TestClient):
    """
    Test that successful login persists an active session row in sessions table.
    """
    db_path, _ = seeded_db
    response = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, is_active FROM sessions WHERE id = ?", (session_id,)
    )
    session = cursor.fetchone()
    assert session is not None
    assert session["id"] == session_id
    assert session["is_active"] == 1
    conn.close()
