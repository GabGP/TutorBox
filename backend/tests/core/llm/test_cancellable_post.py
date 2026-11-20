"""Tests for the stoppable POST to the local LLM server."""

import http.client
import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from core.llm import LLMCallCancelled, LocalSLMClient, cancellable_post
from core.llm.cancellable_post import post_json_until_stopped

COMPLETION = {"choices": [{"message": {"content": "hola"}}]}


class _FakeLLMServer(ThreadingHTTPServer):
    """Answers after `answer_delay` seconds, or reports that the client left."""

    answer_delay: float = 0.0
    answer_status: int = 200
    client_left = threading.Event()
    received_bodies: list[dict]


class _Handler(BaseHTTPRequestHandler):
    server: _FakeLLMServer

    def log_message(self, *_args) -> None:
        """Keeps the test output quiet."""

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        self.server.received_bodies.append(json.loads(self.rfile.read(length)))
        deadline = time.monotonic() + self.server.answer_delay
        while time.monotonic() < deadline:
            # A closed client shows up as end-of-stream on the read side.
            self.connection.settimeout(0.05)
            try:
                if self.connection.recv(1) == b"":
                    self.server.client_left.set()
                    return
            except TimeoutError:
                continue
        body = json.dumps(COMPLETION).encode()
        self.send_response(self.server.answer_status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def llm_server(monkeypatch) -> Iterator[_FakeLLMServer]:
    """Starts a local fake LLM server on a free port."""
    monkeypatch.setattr(cancellable_post, "STOP_POLL_SECONDS", 0.02)
    server = _FakeLLMServer(("127.0.0.1", 0), _Handler)
    server.client_left = threading.Event()
    server.received_bodies = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def _url(server: _FakeLLMServer) -> str:
    return f"http://127.0.0.1:{server.server_address[1]}/v1/chat/completions"


def test_returns_answer_when_never_stopped(llm_server: _FakeLLMServer):
    """A request nobody stops returns the server's JSON."""
    answer = post_json_until_stopped(
        _url(llm_server), {"model": "m"}, 5.0, should_stop=lambda: False
    )
    assert answer == COMPLETION
    assert llm_server.received_bodies == [{"model": "m"}]


def test_stop_closes_the_connection_while_the_model_thinks(llm_server):
    """Stopping mid-request raises at once and the server sees the client leave."""
    llm_server.answer_delay = 5.0
    stop_at = time.monotonic() + 0.2
    started = time.monotonic()

    with pytest.raises(LLMCallCancelled):
        post_json_until_stopped(
            _url(llm_server), {}, 10.0, should_stop=lambda: time.monotonic() > stop_at
        )

    assert time.monotonic() - started < 2.0
    assert llm_server.client_left.wait(2.0)


def test_answer_that_arrives_after_stop_is_discarded(monkeypatch):
    """A stop that lands as the answer arrives still raises LLMCallCancelled."""

    def always_stopped() -> bool:
        return True

    def fake_watch(_connection, should_stop, _finished, stop_requested) -> None:
        if should_stop():
            stop_requested.set()

    monkeypatch.setattr(cancellable_post, "_watch_for_stop", fake_watch)
    server = _FakeLLMServer(("127.0.0.1", 0), _Handler)
    server.received_bodies = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with pytest.raises(LLMCallCancelled):
            post_json_until_stopped(_url(server), {}, 5.0, always_stopped)
    finally:
        server.shutdown()
        server.server_close()


def test_http_error_status_raises_runtime_error(llm_server: _FakeLLMServer):
    """A 5xx answer becomes a RuntimeError naming the status and the body."""
    llm_server.answer_status = 500
    with pytest.raises(RuntimeError, match="LocalSLM HTTP 500"):
        post_json_until_stopped(_url(llm_server), {}, 5.0, lambda: False)


def test_unreachable_server_raises_runtime_error():
    """A refused connection that nobody stopped is a plain request failure."""
    with pytest.raises(RuntimeError, match="LocalSLM request failed"):
        post_json_until_stopped(
            "http://127.0.0.1:9/v1/chat/completions", {}, 1.0, lambda: False
        )


def test_https_url_and_query_pick_the_matching_connection():
    """HTTPS URLs open an HTTPSConnection and keep the query in the path."""
    connection, path = cancellable_post._open_connection(
        "https://llm.local:8443/v1/chat?x=1", 3.0
    )
    assert isinstance(connection, http.client.HTTPSConnection)
    assert path == "/v1/chat?x=1"


def test_shut_down_socket_tolerates_unopened_connection():
    """Stopping before the socket exists is a no-op."""
    connection = http.client.HTTPConnection("127.0.0.1", 9)
    cancellable_post._shut_down_socket(connection)
    assert connection.sock is None


def test_local_client_routes_stoppable_calls(llm_server: _FakeLLMServer):
    """LocalSLMClient uses the stoppable POST when given `should_stop`."""
    base_url = f"http://127.0.0.1:{llm_server.server_address[1]}/v1"
    client = LocalSLMClient(base_url=base_url, model="m", timeout_seconds=5)
    assert client.generate("s", "u", should_stop=lambda: False) == "hola"
