"""Tests for the startup bootstrap teacher seeder."""

from src.core.db.seed_users import seed_teacher


def test_seed_teacher_inserts_once(temp_db, monkeypatch):
    """First run creates a teacher with the configured username; second run is a no-op."""
    db_path, conn = temp_db
    monkeypatch.setenv("SEED_TEACHER_USERNAME", "profe")
    monkeypatch.setenv("SEED_TEACHER_PIN", "4321")

    assert seed_teacher(db_path) is True
    assert seed_teacher(db_path) is False

    rows = conn.execute(
        "SELECT role, hashed_pin, must_change_pin FROM users WHERE username = 'profe'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["role"] == "teacher"
    assert rows[0]["must_change_pin"] == 0
    assert "4321" not in rows[0]["hashed_pin"], "PIN must be stored hashed"


def test_seed_teacher_can_log_in_and_use_teacher_endpoints(temp_db, client):
    """App startup seeds teacher1/1234; it authenticates and passes the teacher guard."""
    db_path, _ = temp_db
    assert seed_teacher(db_path) is False, "lifespan already seeded the teacher"

    login = client.post(
        "/api/v1/auth/login", json={"username": "teacher1", "pin": "1234"}
    )
    assert login.status_code == 200
    assert login.json()["must_change_pin"] is False

    headers = {"Authorization": f"Bearer {login.json()['session_id']}"}
    response = client.get("/api/v1/quiz/generation-logs", headers=headers)
    assert response.status_code == 200


def test_seed_teacher_disabled_by_empty_pin(temp_db, monkeypatch):
    """An empty SEED_TEACHER_PIN switches seeding off."""
    db_path, conn = temp_db
    monkeypatch.setenv("SEED_TEACHER_PIN", "")

    assert seed_teacher(db_path) is False
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_seed_teacher_skips_existing_username(staff_db):
    """Never overwrites a user that already holds the configured username."""
    db_path, conn = staff_db
    before = conn.execute(
        "SELECT hashed_pin FROM users WHERE username = 'teacher1'"
    ).fetchone()[0]

    assert seed_teacher(db_path) is False

    after = conn.execute(
        "SELECT hashed_pin FROM users WHERE username = 'teacher1'"
    ).fetchone()[0]
    assert before == after
