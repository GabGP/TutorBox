"""Unit tests for the vote transport decision: taken from the caller's session only."""

from api.session.transport import resolve_vote_transport
from core.security.auth_session import AuthContext

CLICKER_ID = "ESP32-A4CF12"


def _context(device_id: str | None) -> AuthContext:
    return AuthContext(
        user_id=7,
        username="student1",
        role="student",
        session_id="digest-of-a-bearer-token",
        must_change_pin=False,
        device_id=device_id,
    )


def test_a_session_issued_to_a_clicker_votes_as_hardware_with_its_device():
    assert resolve_vote_transport(_context(CLICKER_ID)) == ("hardware", CLICKER_ID)


def test_a_session_without_a_device_votes_as_web_with_no_device():
    assert resolve_vote_transport(_context(None)) == ("web", None)
