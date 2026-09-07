"""Domain exceptions for quiz session engine and persistence."""


class SessionError(Exception):
    """Base exception for all session domain errors."""


class VoteAlreadyCastError(SessionError):
    """Raised when a student attempts to vote more than once in the same round."""

    def __init__(self, message: str, round_id: str, student_id: int) -> None:
        super().__init__(message)
        self.round_id = round_id
        self.student_id = student_id


class SessionNotFoundError(SessionError):
    """Raised when the requested quiz session does not exist."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Quiz session '{session_id}' not found.")
        self.session_id = session_id


class RoundNotFoundError(SessionError):
    """Raised when the requested quiz round does not exist."""

    def __init__(self, round_id: str) -> None:
        super().__init__(f"Quiz round '{round_id}' not found.")
        self.round_id = round_id


class InvalidSessionStateError(SessionError):
    """Raised when an operation is invalid for current session state."""


class InvalidRoundStateError(SessionError):
    """Raised when an operation (e.g. voting) occurs in non-open round state."""


class InvalidOptionError(SessionError):
    """Raised when a selected option key is not valid (must be A, B, C, or D)."""


class TransportError(SessionError):
    """Raised when dispatching an event through VoteTransport fails."""
