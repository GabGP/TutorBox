"""Concrete LLM client for local llama.cpp / OpenAI-compatible completion server."""

import json
import os
import urllib.error
import urllib.request
from typing import Any

from llm.base import LLMClient

DEFAULT_SLM_BASE_URL: str = "http://127.0.0.1:8080/v1"
DEFAULT_SLM_MODEL_NAME: str = "default"
DEFAULT_SLM_TEMPERATURE: float = 0.7
DEFAULT_SLM_TIMEOUT_SECONDS: float = 60.0

__all__ = [
    "DEFAULT_SLM_BASE_URL",
    "DEFAULT_SLM_MODEL_NAME",
    "DEFAULT_SLM_TEMPERATURE",
    "DEFAULT_SLM_TIMEOUT_SECONDS",
    "LocalSLMClient",
]


class LocalSLMClient(LLMClient):
    """Client for local llama.cpp / OpenAI-compatible completion server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("SLM_BASE_URL", DEFAULT_SLM_BASE_URL)
        ).rstrip("/")
        self.model = model or os.environ.get("SLM_MODEL_NAME", DEFAULT_SLM_MODEL_NAME)
        self.temperature = self._resolve_temperature(temperature)
        self.timeout = self._resolve_timeout(timeout_seconds)

    @staticmethod
    def _resolve_temperature(temperature: float | None) -> float:
        """Resolves sampling temperature with environment override and fallback."""
        if temperature is not None:
            return temperature
        raw_env_temp = os.environ.get("SLM_TEMPERATURE")
        try:
            return (
                float(raw_env_temp)
                if raw_env_temp is not None
                else DEFAULT_SLM_TEMPERATURE
            )
        except ValueError:
            return DEFAULT_SLM_TEMPERATURE

    @staticmethod
    def _resolve_timeout(timeout_seconds: float | None) -> float:
        """Resolves request timeout with environment override and fallback."""
        if timeout_seconds is not None:
            return float(timeout_seconds)
        raw_env_timeout = os.environ.get("SLM_TIMEOUT_SECONDS") or os.environ.get(
            "SLM_TIMEOUT"
        )
        try:
            return (
                float(raw_env_timeout)
                if raw_env_timeout is not None
                else DEFAULT_SLM_TIMEOUT_SECONDS
            )
        except ValueError:
            return DEFAULT_SLM_TIMEOUT_SECONDS

    def _build_request_payload(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """Constructs OpenAI-compatible completion request body."""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
        }

    def _execute_http_post(
        self, endpoint_url: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatches an HTTP POST request and parses the returned JSON payload."""
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
                return json.loads(http_response.read().decode("utf-8"))
        except urllib.error.HTTPError as http_error:
            error_body = http_error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LocalSLM HTTP {http_error.code} ({http_error.reason}): {error_body}"
            ) from http_error
        except Exception as request_error:
            raise RuntimeError(
                f"LocalSLM request failed: {request_error}"
            ) from request_error

    @staticmethod
    def _parse_completion_response(response_data: dict[str, Any]) -> str:
        """Extracts the assistant message content from the API response payload."""
        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list):
            raise TypeError("Malformed response from LocalSLM: missing 'choices' list.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise TypeError(
                "Malformed response from LocalSLM: choice entry is not an object."
            )
        message = first_choice.get("message")
        if not isinstance(message, dict) or "content" not in message:
            raise TypeError(
                "Malformed response from LocalSLM: missing 'message.content'."
            )
        return str(message["content"])

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = self._build_request_payload(system_prompt, user_prompt)
        response_data = self._execute_http_post(endpoint_url, payload)
        return self._parse_completion_response(response_data)
