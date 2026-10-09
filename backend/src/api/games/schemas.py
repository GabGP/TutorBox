"""Pydantic schemas for Mode 3 game event ingestion."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from modes.games.events import CLIENT_ID_PATTERN

__all__ = ["MAX_EVENTS_PER_BATCH", "GameEventBatch", "GameEventBatchResult"]

MAX_EVENTS_PER_BATCH = 200


class GameEventBatch(BaseModel):
    """What a phone posts: who it is and the answers it has not confirmed yet."""

    model_config = ConfigDict(extra="ignore")

    install_id: str = Field(
        pattern=CLIENT_ID_PATTERN,
        description="Random id the app generates once and keeps: tells one phone or browser from another.",
    )
    # Deliberately Any: each event is validated on its own in ingest_events, so one
    # malformed event is rejected alone instead of failing the whole batch.
    events: list[Any] = Field(
        min_length=1,
        max_length=MAX_EVENTS_PER_BATCH,
        description="Each item is validated on its own; see GameEvent.",
    )


class GameEventBatchResult(BaseModel):
    """How many events were new, already stored or malformed, and each one's status in order."""

    accepted: int
    duplicates: int
    rejected: int
    results: list[Literal["accepted", "duplicate", "rejected"]]
