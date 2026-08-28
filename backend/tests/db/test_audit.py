import pytest

from src.db.audit import VALID_ACTIONS, record_audit


def test_record_audit_valid_actions(temp_db):
    """
    record_audit successfully persists rows for all defined valid actions.
    """
    _, conn = temp_db
    for action in VALID_ACTIONS:
        record_audit(
            conn,
            actor_user_id=1,
            action=action,
            target_user_id=2,
        )
    conn.commit()

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    assert cursor.fetchone()[0] == len(VALID_ACTIONS)


def test_record_audit_none_actor_and_target(temp_db):
    """
    record_audit accepts None for actor_user_id (e.g. self-signup) and target_user_id.
    """
    _, conn = temp_db
    record_audit(conn, actor_user_id=None, action="signup", target_user_id=None)
    conn.commit()

    cursor = conn.cursor()
    cursor.execute("SELECT actor_user_id, action, target_user_id FROM audit_logs")
    row = cursor.fetchone()
    assert row["actor_user_id"] is None
    assert row["action"] == "signup"
    assert row["target_user_id"] is None


def test_record_audit_invalid_action_raises_value_error(temp_db):
    """
    record_audit raises ValueError when given an unknown action.
    """
    _, conn = temp_db
    with pytest.raises(ValueError, match="Unknown audit action"):
        record_audit(conn, actor_user_id=1, action="invalid_action_xyz")
