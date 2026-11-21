"""Staff buttons for the quiz model: a question batch loads it, and unloads it when it ends."""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.llm.residency import (
    ModelResidencyManager,
    ModelResidencyResult,
    get_model_residency,
)
from core.security import AuthContext, require_roles

__all__ = ["router"]

router = APIRouter()

Staff = Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]
Residency = Annotated[ModelResidencyManager, Depends(get_model_residency)]


@router.post("/model/load", response_model=ModelResidencyResult)
def load_quiz_model(_ctx: Staff, residency: Residency) -> ModelResidencyResult:
    """Loads the quiz model before a batch; the batch unloads it when it finishes."""
    return residency.load_quiz()


@router.post("/model/unload", response_model=ModelResidencyResult)
def unload_quiz_model(_ctx: Staff, residency: Residency) -> ModelResidencyResult:
    """Unloads the quiz model at the end of a batch, or when the batch was cancelled."""
    return residency.release_quiz()
