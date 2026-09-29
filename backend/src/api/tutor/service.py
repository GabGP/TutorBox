"""Process-wide tutor, turn gate and roster, built on first use (TUTOR_* settings).

All are FastAPI dependencies so tests can swap in a tutor with a mock model.
"""

from functools import lru_cache

from api.tutor.gate import TurnGate
from api.tutor.roster import TutorRoster
from core.config.tutor_settings import load_tutor_config
from modes.socratic import (
    ConversationStore,
    SocraticTutor,
    TutorGateway,
    TutorSLMClient,
)

__all__ = ["get_roster", "get_turn_gate", "get_tutor"]


@lru_cache(maxsize=1)
def get_tutor() -> SocraticTutor:
    config = load_tutor_config()
    gateway = TutorGateway(
        TutorSLMClient(config), config.max_concurrent, config.queue_seconds
    )
    return SocraticTutor(gateway, ConversationStore())


@lru_cache(maxsize=1)
def get_turn_gate() -> TurnGate:
    return TurnGate(load_tutor_config().turns_per_minute)


@lru_cache(maxsize=1)
def get_roster() -> TutorRoster:
    return TutorRoster()
