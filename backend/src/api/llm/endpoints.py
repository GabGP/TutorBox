"""API router exposing explicit LLM model lifecycle proxy endpoints."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from api.llm.proxy import proxy_llm_load, proxy_llm_status, proxy_llm_unload
from api.llm.schemas import LLMActionResponse, LLMLoadRequest, LLMStatusResponse
from core.security import AuthContext, require_roles

logger = logging.getLogger(__name__)
router = APIRouter()

__all__ = ["router"]


@router.post(
    "/load",
    response_model=LLMActionResponse,
    status_code=status.HTTP_200_OK,
)
def load_llm_model(
    _ctx: Annotated[AuthContext, Depends(require_roles("admin"))],
    payload: LLMLoadRequest | None = None,
) -> LLMActionResponse:
    """Triggers model loading in local llama-server."""
    model_name = payload.model if payload else None
    result = proxy_llm_load(model_name)
    return LLMActionResponse(
        status=result.get("status", "ok"),
        detail=str(result.get("detail", "Model loaded successfully")),
    )


@router.post(
    "/unload",
    response_model=LLMActionResponse,
    status_code=status.HTTP_200_OK,
)
def unload_llm_model(
    _ctx: Annotated[AuthContext, Depends(require_roles("admin"))],
) -> LLMActionResponse:
    """Triggers model unloading from GPU/RAM in local llama-server."""
    result = proxy_llm_unload()
    return LLMActionResponse(
        status=result.get("status", "ok"),
        detail=str(result.get("detail", "Model unloaded successfully")),
    )


@router.get(
    "/status",
    response_model=LLMStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_llm_status(
    _ctx: Annotated[AuthContext, Depends(require_roles("admin"))],
) -> LLMStatusResponse:
    """Fetches model status directly from local llama-server."""
    result = proxy_llm_status()
    models_list: list[dict[str, Any]] = (
        result.get("models")
        or result.get("data")
        or ([result] if isinstance(result, dict) else [])
    )
    return LLMStatusResponse(
        status=result.get("status", "ok"),
        models=models_list,
    )
