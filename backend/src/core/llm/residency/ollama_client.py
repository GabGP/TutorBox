"""Ollama's native model API: load a model and keep it, unload it, list what is in memory."""

import time
from typing import Any

from core.llm.residency.ollama_transport import request_json

__all__ = ["OllamaResidencyClient", "ollama_server_root"]

NANOSECONDS_PER_MILLISECOND = 1_000_000


def ollama_server_root(base_url: str) -> str:
    """The server address behind SLM_BASE_URL, without the OpenAI-compatible /v1 suffix."""
    return base_url.rstrip("/").removesuffix("/v1")


class OllamaResidencyClient:
    """Talks to Ollama's /api/generate (load and unload) and /api/ps (what is loaded)."""

    def __init__(self, server_root: str, timeout_seconds: float) -> None:
        self._root = server_root.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def load(self, model_name: str) -> float:
        """Loads the model and keeps it (keep_alive -1); returns how long loading took, in ms."""
        started_at = time.monotonic()
        answer = self._generate({"model": model_name, "keep_alive": -1})
        wall_clock_ms = (time.monotonic() - started_at) * 1000
        server_load_ns = answer.get("load_duration")
        if isinstance(server_load_ns, (int, float)):
            return server_load_ns / NANOSECONDS_PER_MILLISECOND
        return wall_clock_ms

    def unload(self, model_name: str) -> None:
        """Drops the model from memory now (keep_alive 0)."""
        self._generate({"model": model_name, "keep_alive": 0})

    def resident_models(self) -> set[str]:
        """Names of the models Ollama holds in memory right now."""
        answer = request_json(
            "GET", f"{self._root}/api/ps", None, self._timeout_seconds
        )
        names: set[str] = set()
        for entry in _as_list(answer.get("models")):
            names.update(str(entry[key]) for key in ("name", "model") if key in entry)
        return names

    def _generate(self, body: dict[str, Any]) -> dict[str, Any]:
        # stream false: one JSON object instead of Ollama's line-by-line stream.
        return request_json(
            "POST",
            f"{self._root}/api/generate",
            {**body, "stream": False},
            self._timeout_seconds,
        )


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict)]
