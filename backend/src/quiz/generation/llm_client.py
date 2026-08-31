import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generates completion text given system and user prompts."""


class MockLLMClient(LLMClient):
    """Mock LLM client for unit tests and local simulation."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses: list[str] = list(responses) if responses else []
        self._index: int = 0
        self.call_history: list[tuple[str, str]] = []

    def add_response(self, response: str) -> None:
        self._responses.append(response)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.call_history.append((system_prompt, user_prompt))
        if not self._responses:
            raise RuntimeError("MockLLMClient has no configured responses.")
        response = self._responses[min(self._index, len(self._responses) - 1)]
        if self._index < len(self._responses) - 1:
            self._index += 1
        return response


class LocalSLMClient(LLMClient):
    """Client for local llama.cpp / OpenAI-compatible completion server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("SLM_BASE_URL", "http://127.0.0.1:8080/v1")
        ).rstrip("/")
        self.model = model or os.environ.get("SLM_MODEL_NAME", "default")
        self.timeout = timeout_seconds

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        encoded_body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            endpoint_url,
            data=encoded_body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                http_request, timeout=self.timeout
            ) as http_response:
                response_data = json.loads(http_response.read().decode("utf-8"))
                return response_data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as http_error:
            error_body = http_error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LocalSLM HTTP {http_error.code} ({http_error.reason}): {error_body}"
            ) from http_error
        except Exception as request_error:
            raise RuntimeError(
                f"LocalSLM request failed: {request_error}"
            ) from request_error
