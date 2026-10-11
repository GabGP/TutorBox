"""Which transport a vote arrived through, decided from the caller's session, never from the request body."""

from typing import NamedTuple

from core.security.auth_session import AuthContext
from modes.quiz.session.models import TransportType

__all__ = ["VoteOrigin", "resolve_vote_transport"]


class VoteOrigin(NamedTuple):
    transport_type: str
    device_id: str | None


def resolve_vote_transport(ctx: AuthContext) -> VoteOrigin:
    """A token issued to a clicker votes as `hardware` with that clicker's id; any other token votes as `web`."""
    if ctx.device_id is None:
        return VoteOrigin(transport_type=TransportType.WEB.value, device_id=None)
    return VoteOrigin(
        transport_type=TransportType.HARDWARE.value, device_id=ctx.device_id
    )
