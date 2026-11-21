"""Fakes for residency tests: no test ever reaches a real Ollama server."""

import io
import json
import urllib.error
from email.message import Message
from typing import Any, Self

from core.llm.residency.manager import ModelResidencyManager


class FakeHTTPResponse:
    """What urllib.request.urlopen returns, as a context manager."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


class FakeOllamaHTTP:
    """Replaces urllib.request.urlopen: records every request and answers by route.

    Routes are keyed by (method, path). A route may hold a dict (answered as JSON) or an
    exception instance (raised instead), so each test describes the server it needs.
    """

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict[str, Any] | None]] = []
        self.routes: dict[tuple[str, str], Any] = {}
        self.headers: list[dict[str, str]] = []

    def __call__(
        self, http_request: Any, timeout: float | None = None
    ) -> FakeHTTPResponse:
        path = http_request.full_url.split("://", 1)[1].split("/", 1)[1]
        payload = json.loads(http_request.data) if http_request.data else None
        self.requests.append((http_request.get_method(), "/" + path, payload))
        self.headers.append(dict(http_request.header_items()))
        answer = self.routes[(http_request.get_method(), "/" + path)]
        if isinstance(answer, BaseException):
            raise answer
        return FakeHTTPResponse(json.dumps(answer).encode("utf-8"))


def http_status_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    """An HTTPError with a readable body, as a refusing server would send."""
    return urllib.error.HTTPError(
        url="http://ollama.test",
        code=code,
        msg="refused",
        hdrs=Message(),
        fp=io.BytesIO(body),
    )


class FakeResidencyClient:
    """Stands in for OllamaResidencyClient at the manager level; records every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []
        self.resident: set[str] = set()
        self.load_error: Exception | None = None
        self.unload_error: Exception | None = None
        self.list_error: Exception | None = None
        self.gpu_error: Exception | None = None
        self.gpu_share: int | None = 100
        self.load_ms = 3200.0

    def load(self, model_name: str) -> float:
        self.calls.append(("load", model_name))
        if self.load_error is not None:
            raise self.load_error
        return self.load_ms

    def unload(self, model_name: str) -> None:
        self.calls.append(("unload", model_name))
        if self.unload_error is not None:
            raise self.unload_error

    def resident_models(self) -> set[str]:
        self.calls.append(("resident", None))
        if self.list_error is not None:
            raise self.list_error
        return set(self.resident)

    def gpu_percent(self, model_name: str) -> int | None:
        self.calls.append(("gpu", model_name))
        if self.gpu_error is not None:
            raise self.gpu_error
        return self.gpu_share

    def called(self) -> list[tuple[str, str | None]]:
        return [call for call in self.calls if call[0] not in ("resident", "gpu")]


class FakeCountdown:
    """A countdown that only fires when a test says so."""

    def __init__(self, interval: float, callback: Any) -> None:
        self.interval = interval
        self.callback = callback
        self.daemon = False
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def expire(self) -> None:
        self.callback()


class FakeCountdowns:
    """Passed as the timer factory; keeps every countdown the code created, in order."""

    def __init__(self) -> None:
        self.created: list[FakeCountdown] = []

    def __call__(self, interval: float, callback: Any) -> FakeCountdown:
        countdown = FakeCountdown(interval, callback)
        self.created.append(countdown)
        return countdown

    @property
    def latest(self) -> FakeCountdown:
        return self.created[-1]


QUIZ_MODEL = "qwen2.5:3b"
TUTOR_MODEL = "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0"


def build_fake_manager(
    client: FakeResidencyClient | None = None, countdowns: FakeCountdowns | None = None
) -> ModelResidencyManager:
    """A manager that is switched on and talks to fakes only (used by the API tests)."""
    return ModelResidencyManager(
        client or FakeResidencyClient(),
        quiz_model=QUIZ_MODEL,
        tutor_model=TUTOR_MODEL,
        enabled=True,
        quiz_idle_seconds=90.0,
        timer_factory=countdowns or FakeCountdowns(),
    )


__all__ = [
    "QUIZ_MODEL",
    "TUTOR_MODEL",
    "FakeCountdown",
    "FakeCountdowns",
    "FakeHTTPResponse",
    "FakeOllamaHTTP",
    "FakeResidencyClient",
    "build_fake_manager",
    "http_status_error",
]
