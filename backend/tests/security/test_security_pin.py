import logging

from fastapi.testclient import TestClient

from src.security.auth import hash_pin
from tests.conftest import auth_headers


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
        client.post("/api/v1/auth/login", json={"username": "student1", "pin": "1234"})

        # 2. Attempt failed login (wrong PIN)
        client.post("/api/v1/auth/login", json={"username": "student1", "pin": "9999"})

        # 3. Attempt failed login (unknown user)
        client.post(
            "/api/v1/auth/login", json={"username": "unknown_student", "pin": "8888"}
        )

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


def test_plain_text_pin_never_logged_during_signup(temp_db, client: TestClient, caplog):
    """
    SECURITY PROOF 4:
    Verify that during signup attempts (successful, conflict, or malformed),
    plain-text PINs are never output to any logging handler.
    """
    sensitive_pins = ["7777", "8888"]

    with caplog.at_level(logging.DEBUG):
        # 1. Successful signup
        client.post(
            "/signup", json={"username": "sec_student", "pin": sensitive_pins[0]}
        )
        # 2. Duplicate signup attempt
        client.post(
            "/signup", json={"username": "sec_student", "pin": sensitive_pins[1]}
        )

    for record in caplog.records:
        log_message = record.getMessage()
        for sensitive_pin in sensitive_pins:
            assert sensitive_pin not in log_message, (
                f"Security violation: Sensitive PIN '{sensitive_pin}' logged in signup: '{log_message}'"
            )


def test_plain_text_pin_never_logged_during_credential_change(
    seeded_db, client: TestClient, caplog
):
    """
    SECURITY PROOF 5:
    Verify that during PIN changes and username changes,
    neither current nor new plain-text PINs are logged.
    """
    sensitive_pins = ["1234", "9876", "1111"]
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    with caplog.at_level(logging.DEBUG):
        # 1. Successful PIN change
        client.patch(
            "/users/me/pin",
            headers=headers,
            json={"current_pin": sensitive_pins[0], "new_pin": sensitive_pins[1]},
        )
        # 2. Failed username change with bad PIN
        client.patch(
            "/users/me/username",
            headers=headers,
            json={
                "current_pin": sensitive_pins[2],
                "new_username": "new_student_name",
            },
        )

    for record in caplog.records:
        log_message = record.getMessage()
        for sensitive_pin in sensitive_pins:
            assert sensitive_pin not in log_message, (
                f"Security violation: Sensitive PIN '{sensitive_pin}' logged in credential change: '{log_message}'"
            )


def test_plain_text_pin_never_logged_during_staff_user_creation(
    staff_db, client: TestClient, caplog
):
    """
    SECURITY PROOF 6:
    Verify that when staff creates a user account, the initial PIN is never logged.
    """
    sensitive_pin = "3333"
    headers = auth_headers(client, "admin1", "1234")

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/users",
            headers=headers,
            json={
                "username": "staff_created_user",
                "pin": sensitive_pin,
                "role": "student",
            },
        )

    for record in caplog.records:
        log_message = record.getMessage()
        assert sensitive_pin not in log_message, (
            f"Security violation: Sensitive PIN '{sensitive_pin}' logged in staff user creation: '{log_message}'"
        )


def test_session_id_never_logged_across_endpoints(
    seeded_db, client: TestClient, caplog
):
    """
    SECURITY PROOF 7:
    Bearer session identifier must never appear in any log output across
    login, user profile check, and logout workflows.
    """
    with caplog.at_level(logging.DEBUG):
        # 1. Login
        login_res = client.post(
            "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
        )
        assert login_res.status_code == 200
        session_id = login_res.json()["session_id"]
        headers = {"Authorization": f"Bearer {session_id}"}

        # 2. Profile
        profile_res = client.get("/api/v1/users/me", headers=headers)
        assert profile_res.status_code == 200

        # 3. Logout
        logout_res = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200

    for record in caplog.records:
        assert session_id not in record.getMessage(), (
            f"Security violation: session ID leaked in log: '{record.getMessage()}'"
        )
