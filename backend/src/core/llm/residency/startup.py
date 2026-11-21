"""Startup reconciliation: runs in a background thread so the backend never waits on Ollama."""

import logging
import threading

from core.db.database import get_db
from core.db.mode_repository import get_mode
from core.llm.residency.factory import get_model_residency

logger = logging.getLogger(__name__)

__all__ = ["start_residency_reconcile"]


def start_residency_reconcile() -> threading.Thread | None:
    """Starts the reconcile for the saved mode; None when residency management is off."""
    if not get_model_residency().enabled:
        return None
    thread = threading.Thread(
        target=_reconcile_with_saved_mode, name="model-residency", daemon=True
    )
    thread.start()
    return thread


def _reconcile_with_saved_mode() -> None:
    try:
        with get_db() as conn:
            saved_mode = get_mode(conn)
        result = get_model_residency().reconcile(saved_mode)
        logger.info("Startup model residency for %s: %s.", result.model, result.action)
    except Exception:
        logger.exception("Startup model residency failed.")
