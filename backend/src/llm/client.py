"""Concrete LLM client for local llama.cpp / OpenAI-compatible completion server."""

import json
import urllib.error
import urllib.request
from typing import Any

from config import (
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
    get_settings,
)
from llm.base import LLMClient

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
        settings = get_settings(reload=True).llm
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.model = model or settings.model_name
        self.temperature = (
            temperature if temperature is not None else settings.temperature
        )
        self.timeout = (
            float(timeout_seconds)
            if timeout_seconds is not None
            else settings.timeout_seconds
        )

    def _build_request_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Constructs OpenAI-compatible completion request body."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        return payload

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

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = self._build_request_payload(
            system_prompt, user_prompt, response_format=response_format
        )
        response_data = self._execute_http_post(endpoint_url, payload)
        return self._parse_completion_response(response_data)
