"""The appliance state a memory release must respect: the saved mode and whether a game runs."""

from core.db.database import get_db
from core.db.mode_repository import ApplianceMode, get_mode
from core.db.session_repository import get_current_quiz_session
from modes.quiz.session.models import SessionStatus

__all__ = ["quiz_game_running", "read_saved_mode"]


def read_saved_mode() -> ApplianceMode:
    """The mode the teacher saved on the appliance."""
    with get_db() as conn:
        return get_mode(conn)


def quiz_game_running() -> bool:
    """True while the newest quiz session is active (a lobby waits for players and needs no voice yet)."""
    with get_db() as conn:
        session = get_current_quiz_session(conn)
    return session is not None and session.status == SessionStatus.ACTIVE.value
