"""FastAPI router for quiz generation telemetry querying and metrics aggregation."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from db.database import get_db
from db.quiz_telemetry import (
    get_generation_summary_metrics,
    list_generation_logs,
)
from security import AuthContext, require_roles

router = APIRouter()


class GenerationLogItem(BaseModel):
    id: int
    question_id: str | None = None
    user_id: int
    topic: str
    subconcept: str | None = None
    model_name: str
    attempts: int
    duration_ms: float
    success: bool
    rejection_history: list[str] = Field(default_factory=list)
    created_at: str | None = None


class GenerationLogsResponse(BaseModel):
    logs: list[GenerationLogItem]
    total: int


class GenerationMetricsResponse(BaseModel):
    total_generations: int
    successful_generations: int
    failed_generations: int
    success_rate: float
    avg_attempts: float
    avg_duration_ms: float


@router.get("/generation-logs", response_model=GenerationLogsResponse)
def get_generation_logs(
    _: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    topic: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    success: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GenerationLogsResponse:
    """Lists telemetry logs for quiz generation attempts."""
    with get_db() as conn:
        logs = list_generation_logs(
            conn,
            user_id=user_id,
            topic=topic,
            success=success,
            limit=limit,
            offset=offset,
        )
    return GenerationLogsResponse(
        logs=[GenerationLogItem(**log) for log in logs],
        total=len(logs),
    )


@router.get("/generation-metrics", response_model=GenerationMetricsResponse)
def get_generation_metrics(
    _: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    topic: str | None = Query(default=None),
    model_name: str | None = Query(default=None),
) -> GenerationMetricsResponse:
    """Computes aggregated generation reliability and latency metrics."""
    with get_db() as conn:
        metrics = get_generation_summary_metrics(
            conn, topic=topic, model_name=model_name
        )
    return GenerationMetricsResponse(**metrics)
