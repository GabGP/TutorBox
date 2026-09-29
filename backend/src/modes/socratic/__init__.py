"""Mode 2: Socratic Math Practice Tutor (Week 5).

Provides mobile conversational math practice with strictly Socratic guidance,
deterministic hint escalation ladders (levels 0 to 3), and SymPy math containment.
Only CNB mathematics for 1.º to 5.º primaria is in scope (cnb_matematicas.json).
"""

from modes.socratic.engine import SocraticTutor, TurnResult
from modes.socratic.gateway import TutorGateway, TutorSLMClient
from modes.socratic.state import Conversation, ConversationStore

__all__ = [
    "Conversation",
    "ConversationStore",
    "SocraticTutor",
    "TurnResult",
    "TutorGateway",
    "TutorSLMClient",
]
