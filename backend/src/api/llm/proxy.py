"""HTTP proxy delegating lifecycle commands to local llama-server."""

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from fastapi import HTTPException, status

from core.config import get_settings

logger = logging.getLogger(__name__)

__all__ = ["proxy_llm_load", "proxy_llm_status", "proxy_llm_unload"]


def _get_server_urls() -> tuple[str, float]:
    """Returns the base llama-server URL and request timeout."""
    settings = get_settings().llm
    base = settings.base_url.rstrip("/")
    server_root = base.removesuffix("/v1")
    return server_root, float(settings.timeout_seconds)


def _dispatch_request(
    endpoint: str, data: dict[str, Any] | None = None, method: str = "GET"
) -> dict[str, Any]:
    """Dispatches HTTP request to llama-server and parses JSON response."""
    server_root, timeout = _get_server_urls()
    url = f"{server_root}{endpoint}"
    encoded = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}

    req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {"status": "ok"}
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="replace")[:200]
        logger.warning(
            "LLM server returned HTTP %s on %s: %s", err.code, endpoint, err_body
        )
        raise HTTPException(
            status_code=err.code, detail=f"LLM server error ({err.code}): {err_body}"
        ) from err
    except (urllib.error.URLError, OSError, TimeoutError) as err:
        logger.warning("LLM server unreachable on %s: %s", endpoint, err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local LLM server is unreachable.",
        ) from err


def proxy_llm_load(model: str | None = None) -> dict[str, Any]:
    """Proxies model load request to llama-server."""
    payload = {"model": model} if model else {}
    return _dispatch_request("/models/load", data=payload, method="POST")


def proxy_llm_unload() -> dict[str, Any]:
    """Proxies model unload request to llama-server."""
    return _dispatch_request("/models/unload", data={}, method="POST")


def proxy_llm_status() -> dict[str, Any]:
    """Proxies status query to llama-server /models endpoint."""
    return _dispatch_request("/models", method="GET")
