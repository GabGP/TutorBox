"""JSON over HTTP to the Ollama server; every failure leaves as a residency error."""

import json
import urllib.error
import urllib.request
from typing import Any

from core.llm.residency.models import ResidencyError, ResidencyUnsupported

__all__ = ["request_json"]

# Ollama answers 404 for an unknown model and 405 for a wrong method; llama.cpp answers 404
# for every route it does not have, so a 404 without Ollama's model message means "not Ollama".
UNSUPPORTED_STATUS_CODES = frozenset({404, 405})
MAX_ERROR_BODY_CHARACTERS = 200


def request_json(
    method: str, url: str, payload: dict[str, Any] | None, timeout_seconds: float
) -> dict[str, Any]:
    """Sends `payload` (if any) and returns the JSON object the server answers with."""
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if payload is None else {"Content-Type": "application/json"}
    http_request = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            answer = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        raise _classify_http_error(http_error) from http_error
    except OSError as network_error:  # URLError and timeouts are OSError subclasses
        raise ResidencyError(
            f"Ollama is unreachable: {network_error}"
        ) from network_error
    except ValueError as decode_error:  # JSONDecodeError and UnicodeDecodeError
        raise ResidencyError(
            "Ollama answered with something that is not JSON."
        ) from decode_error
    if not isinstance(answer, dict):
        raise ResidencyError("Ollama answered with JSON that is not an object.")
    return answer


def _classify_http_error(http_error: urllib.error.HTTPError) -> ResidencyError:
    """Turns an HTTP refusal into 'not Ollama' or a plain failure, with Ollama's own message."""
    body = _read_error_body(http_error)
    if http_error.code in UNSUPPORTED_STATUS_CODES and not _names_missing_model(body):
        return ResidencyUnsupported(
            f"The server does not answer Ollama's model API (HTTP {http_error.code})."
        )
    message = body[:MAX_ERROR_BODY_CHARACTERS]
    return ResidencyError(f"Ollama answered HTTP {http_error.code}: {message}")


def _read_error_body(http_error: urllib.error.HTTPError) -> str:
    try:
        return http_error.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _names_missing_model(body: str) -> bool:
    """Ollama's 'model ... not found' answer: the server is Ollama, the model is not pulled."""
    return "model" in body and "not found" in body
