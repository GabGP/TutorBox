"""Loads the tutor model in tutor mode and the quiz model during a batch, and unloads them after.

Nothing here raises for a server problem: a refused or unreachable Ollama becomes a result
the caller can show, so a mode switch or a generation never fails because of memory handling.
"""

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

from core.db.mode_repository import ApplianceMode
from core.llm.residency.attempts import attempt_request, outcome, with_gpu_share
from core.llm.residency.models import ModelResidencyResult, ResidencyError
from core.llm.residency.quiz_hold import QuizModelHold, TimerFactory

logger = logging.getLogger(__name__)

__all__ = ["ModelResidencyManager", "ResidencyClient"]


class ResidencyClient(Protocol):
    """What the manager needs from the server (OllamaResidencyClient, or a fake in tests)."""

    def load(self, model_name: str) -> float: ...

    def unload(self, model_name: str) -> None: ...

    def resident_models(self) -> set[str]: ...

    def gpu_percent(self, model_name: str) -> int | None: ...


class ModelResidencyManager:
    """Owns the two model names of the appliance and decides when each one is in memory."""

    def __init__(
        self,
        client: ResidencyClient,
        *,
        quiz_model: str,
        tutor_model: str,
        enabled: bool,
        quiz_idle_seconds: float,
        timer_factory: TimerFactory = threading.Timer,
    ) -> None:
        self._client = client
        self._quiz_model = quiz_model
        self._tutor_model = tutor_model
        self._enabled = enabled
        self._mode: ApplianceMode = "quiz"
        self._mode_lock = threading.Lock()
        self._quiz_hold = QuizModelHold(
            quiz_idle_seconds, self._release_quiz_unless_tutor_needs_it, timer_factory
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def apply_mode(self, mode: ApplianceMode) -> ModelResidencyResult:
        """Loads the tutor model in tutor mode; any other mode unloads it."""
        with self._mode_lock:
            self._mode = mode
            if not self._enabled:
                return outcome(self._tutor_model, "disabled")
            if mode == "tutor":
                return self._load(self._tutor_model)
            if self._tutor_model == self._quiz_model and self._quiz_hold.is_held():
                return outcome(
                    self._tutor_model, "kept", "the quiz is using this model"
                )
            return self._unload(self._tutor_model)

    def load_quiz(self) -> ModelResidencyResult:
        """Loads the quiz model at the start of a batch and arms the idle countdown."""
        if not self._enabled:
            return outcome(self._quiz_model, "disabled")
        result = self._load(self._quiz_model)
        self._quiz_hold.arm()
        return result

    def release_quiz(self) -> ModelResidencyResult:
        """Unloads the quiz model now, at the end of a batch or when it was abandoned."""
        if not self._enabled:
            return outcome(self._quiz_model, "disabled")
        self._quiz_hold.disarm()
        return self._release_quiz_unless_tutor_needs_it()

    @contextmanager
    def generation_in_flight(self) -> Iterator[None]:
        """Wraps one question generation: loads the quiz model if needed, blocks the countdown."""
        if not self._enabled:
            yield
            return
        with self._quiz_hold.generation(self._ensure_quiz_loaded):
            yield

    def reconcile(self, mode: ApplianceMode) -> ModelResidencyResult:
        """At startup: drops a quiz model left in memory by an earlier run, then applies `mode`."""
        if not self._enabled:
            return outcome(self._tutor_model, "disabled")
        if self._quiz_model != self._tutor_model:
            self._unload_leftover_quiz_model()
        return self.apply_mode(mode)

    def _unload_leftover_quiz_model(self) -> None:
        try:
            resident = self._client.resident_models()
        except ResidencyError as error:
            logger.warning(
                "Could not list the models Ollama holds at startup: %s", error
            )
            return
        if self._quiz_model in resident:
            self._unload(self._quiz_model)

    def _ensure_quiz_loaded(self) -> None:
        """A generation loads the quiz model itself when a client skipped /model/load."""
        self._load(self._quiz_model)

    def _release_quiz_unless_tutor_needs_it(self) -> ModelResidencyResult:
        if self._quiz_model == self._tutor_model and self._mode == "tutor":
            return outcome(self._quiz_model, "kept", "the tutor needs this model")
        return self._unload(self._quiz_model)

    def _load(self, model_name: str) -> ModelResidencyResult:
        result = attempt_request(
            model_name, "loaded", lambda: self._client.load(model_name)
        )
        return with_gpu_share(result, lambda: self._client.gpu_percent(model_name))

    def _unload(self, model_name: str) -> ModelResidencyResult:
        return attempt_request(
            model_name, "unloaded", lambda: self._client.unload(model_name)
        )
