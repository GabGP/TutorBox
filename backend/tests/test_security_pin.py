import logging

from fastapi.testclient import TestClient

from src.security.auth import hash_pin


def test_plain_text_pin_not_in_database(temp_db):
    """
    SECURITY PROOF 1:
    Verify that when a user is created with PIN '1234', the plain text string
    '1234' is NEVER stored in the database row or columns.
    """
    _, conn = temp_db
    test_pin = "1234"
    hashed = hash_pin(test_pin)

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin) VALUES (?, ?)",
        ("student_sec_test", hashed),
    )
    conn.commit()

    # Query the user row with raw SQL
    cursor.execute("SELECT * FROM users WHERE username = 'student_sec_test'")
    row = cursor.fetchone()
    assert row is not None

    # Verify no column is named exactly "pin" (only "hashed_pin" should exist)
    row_dict = dict(row)
    assert "hashed_pin" in row_dict
    assert "pin" not in row_dict, "A bare 'pin' column exists — rename to 'hashed_pin'"

    # Strict assertion: The plain text PIN string must not be present in any row value
    for col_name, value in row_dict.items():
        assert test_pin != str(value), f"Plain text PIN leaked in column: {col_name}"
        assert test_pin not in str(value), (
            f"Plain text PIN found as substring in: {col_name}"
        )


def test_plain_text_pin_never_logged_during_login(
    seeded_db, client: TestClient, caplog
):
    """
    SECURITY PROOF 2:
    Verify that during both successful and failed authentication attempts,
    the plain-text PIN '1234' or '9999' is NEVER output to any logging handler.
    """
    sensitive_pins = ["1234", "9999", "8888"]

    with caplog.at_level(logging.DEBUG):
        # 1. Attempt successful login
        client.post("/login", json={"username": "student1", "pin": "1234"})

        # 2. Attempt failed login (wrong PIN)
        client.post("/login", json={"username": "student1", "pin": "9999"})

        # 3. Attempt failed login (unknown user)
        client.post("/login", json={"username": "unknown_student", "pin": "8888"})

    # Inspect all captured log messages
    for record in caplog.records:
        log_message = record.getMessage()
        for sensitive_pin in sensitive_pins:
            assert sensitive_pin not in log_message, (
                f"Security violation: Sensitive PIN '{sensitive_pin}' was logged in message: '{log_message}'"
            )


def test_plain_text_pin_never_logged_during_hashing(caplog):
    """
    SECURITY PROOF 3:
    Verify that the hash_pin and verify_pin functions do not log the plain text PIN.
    """
    sensitive_pin = "4321"

    with caplog.at_level(logging.DEBUG):
        hashed = hash_pin(sensitive_pin)
        from src.security.auth import verify_pin

        verify_pin(sensitive_pin, hashed)
        verify_pin("wrong_pin", hashed)

    for record in caplog.records:
        log_message = record.getMessage()
        assert sensitive_pin not in log_message, (
            f"Security violation: Plain text PIN '{sensitive_pin}' leaked in logger: '{log_message}'"
        )
        assert "wrong_pin" not in log_message
