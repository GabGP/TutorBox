"""JSON POST to the local LLM server that can be stopped while it waits."""

import contextlib
import http.client
import json
import socket
import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

STOP_POLL_SECONDS: float = 0.2


class LLMCallCancelled(Exception):
    """Raised when the caller stopped an LLM request before it answered."""


def _shut_down_socket(connection: http.client.HTTPConnection) -> None:
    """Unblocks the reader and tells the LLM server the client is gone.

    Ollama and llama-server cancel the generation when the connection closes,
    so this frees the model instead of letting it finish an unwanted answer.
    """
    open_socket = connection.sock
    if open_socket is not None:
        with contextlib.suppress(OSError):
            open_socket.shutdown(socket.SHUT_RDWR)


def _watch_for_stop(
    connection: http.client.HTTPConnection,
    should_stop: Callable[[], bool],
    request_finished: threading.Event,
    stop_requested: threading.Event,
) -> None:
    """Polls `should_stop` and shuts the socket down once it turns True."""
    while not request_finished.wait(STOP_POLL_SECONDS):
        if should_stop():
            stop_requested.set()
            _shut_down_socket(connection)


def _open_connection(
    endpoint_url: str, timeout_seconds: float
) -> tuple[http.client.HTTPConnection, str]:
    """Opens an HTTP(S) connection object and returns it with the request path."""
    parts = urlsplit(endpoint_url)
    connection_class = (
        http.client.HTTPSConnection
        if parts.scheme == "https"
        else http.client.HTTPConnection
    )
    path = parts.path + (f"?{parts.query}" if parts.query else "")
    return connection_class(parts.netloc, timeout=timeout_seconds), path


def post_json_until_stopped(
    endpoint_url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    should_stop: Callable[[], bool],
) -> dict[str, Any]:
    """POSTs `payload` and returns the JSON answer, or raises LLMCallCancelled."""
    connection, path = _open_connection(endpoint_url, timeout_seconds)
    request_finished = threading.Event()
    stop_requested = threading.Event()
    watcher = threading.Thread(
        target=_watch_for_stop,
        args=(connection, should_stop, request_finished, stop_requested),
        daemon=True,
    )
    watcher.start()
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException) as request_error:
        if stop_requested.is_set():
            raise LLMCallCancelled("LLM request stopped.") from request_error
        raise RuntimeError(
            f"LocalSLM request failed: {request_error}"
        ) from request_error
    finally:
        request_finished.set()
        connection.close()
        watcher.join()

    if stop_requested.is_set():
        raise LLMCallCancelled("LLM request stopped as it answered.")
    if response.status >= 400:
        raise RuntimeError(
            f"LocalSLM HTTP {response.status} ({response.reason}): {response_body}"
        )
    return json.loads(response_body)
