"""appliance_state: the saved mode and whether a quiz game runs, read from the database."""

from core.db.mode_repository import set_mode
from core.db.session_repository import create_quiz_session, update_quiz_session_status
from core.system_health.appliance_state import quiz_game_running, read_saved_mode


def test_the_saved_mode_is_read_from_the_database(temp_db):
    _, conn = temp_db
    set_mode(conn, "tutor", user_id=None)
    conn.commit()

    assert read_saved_mode() == "tutor"


def test_no_quiz_session_means_no_game(temp_db):
    assert quiz_game_running() is False


def test_a_lobby_is_not_a_running_game(temp_db):
    _, conn = temp_db
    create_quiz_session(conn, "session-lobby", "Fracciones", "fracciones")
    conn.commit()

    assert quiz_game_running() is False


def test_an_active_session_is_a_running_game(temp_db):
    _, conn = temp_db
    create_quiz_session(conn, "session-live", "Fracciones", "fracciones")
    update_quiz_session_status(conn, "session-live", "active")
    conn.commit()

    assert quiz_game_running() is True


def test_a_finished_session_is_not_a_running_game(temp_db):
    _, conn = temp_db
    create_quiz_session(conn, "session-done", "Fracciones", "fracciones")
    update_quiz_session_status(conn, "session-done", "completed")
    conn.commit()

    assert quiz_game_running() is False
