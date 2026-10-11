"""Dialogue turn telemetry for Mode 2 (Week 5).

Labels every tutor turn for the weekly report: the concept practised, the
scaffolding strategy the tutor applied and, on a wrong answer, the error type.
It only reads what the Socratic engine already decided; it never changes a reply.
"""

from modes.socratic.telemetry.concept import Concept, concept_for
from modes.socratic.telemetry.error_type import (
    ERROR_SLUGS,
    UNCLASSIFIED,
    classify_error,
)
from modes.socratic.telemetry.strategy import STRATEGIES, scaffolding_strategy

__all__ = [
    "ERROR_SLUGS",
    "STRATEGIES",
    "UNCLASSIFIED",
    "Concept",
    "classify_error",
    "concept_for",
    "scaffolding_strategy",
]
