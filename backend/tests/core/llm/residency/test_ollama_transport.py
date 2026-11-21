"""request_json (core/llm/residency/ollama_transport.py): every server failure becomes a residency error."""

import io
import json
import urllib.error
import urllib.request
from email.message import Message

import pytest

from core.llm.residency.models import ResidencyError, ResidencyUnsupported
from core.llm.residency.ollama_transport import MAX_ERROR_BODY_CHARACTERS, request_json
from tests.core.llm.residency.fakes import FakeHTTPResponse, http_status_error

URL = "http://127.0.0.1:11434/api/generate"


@pytest.fixture
def urlopen(monkeypatch: pytest.MonkeyPatch):
    """Returns a setter: the next urlopen call answers with `behaviour`."""
    state: dict[str, object] = {}

    def fake_urlopen(http_request, timeout=None):
        state["request"] = http_request
        state["timeout"] = timeout
        behaviour = state["behaviour"]
        if isinstance(behaviour, BaseException):
            raise behaviour
        return behaviour

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    def answer_with(behaviour):
        state["behaviour"] = behaviour
        return state

    return answer_with


def test_posts_json_and_returns_the_answer_object(urlopen):
    state = urlopen(FakeHTTPResponse(b'{"done_reason": "load"}'))

    answer = request_json("POST", URL, {"model": "m"}, timeout_seconds=7.5)

    assert answer == {"done_reason": "load"}
    sent = state["request"]
    assert sent.get_method() == "POST"
    assert json.loads(sent.data) == {"model": "m"}
    assert sent.get_header("Content-type") == "application/json"
    assert state["timeout"] == 7.5


def test_get_sends_no_body_and_no_content_type(urlopen):
    state = urlopen(FakeHTTPResponse(b'{"models": []}'))

    request_json("GET", "http://127.0.0.1:11434/api/ps", None, timeout_seconds=1.0)

    sent = state["request"]
    assert sent.data is None
    assert sent.get_header("Content-type") is None


def test_plain_404_means_the_server_is_not_ollama(urlopen):
    urlopen(http_status_error(404, b"404 page not found"))

    with pytest.raises(ResidencyUnsupported, match="HTTP 404"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


def test_405_means_the_server_is_not_ollama(urlopen):
    urlopen(http_status_error(405, b""))

    with pytest.raises(ResidencyUnsupported, match="HTTP 405"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


def test_404_naming_a_missing_model_is_a_failure_not_unsupported(urlopen):
    body = b'{"error":"model \\"nope:1b\\" not found, try pulling it first"}'
    urlopen(http_status_error(404, body))

    with pytest.raises(ResidencyError, match="not found") as raised:
        request_json("POST", URL, {}, timeout_seconds=1.0)

    assert not isinstance(raised.value, ResidencyUnsupported)


def test_other_http_errors_carry_the_server_message_truncated(urlopen):
    urlopen(http_status_error(500, b"x" * (MAX_ERROR_BODY_CHARACTERS + 50)))

    with pytest.raises(ResidencyError) as raised:
        request_json("POST", URL, {}, timeout_seconds=1.0)

    assert "HTTP 500" in str(raised.value)
    assert str(raised.value).endswith("x" * MAX_ERROR_BODY_CHARACTERS)


def test_unreadable_error_body_is_reported_without_it(urlopen):
    class BrokenBody(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            raise OSError("connection reset")

    urlopen(urllib.error.HTTPError(URL, 500, "boom", Message(), BrokenBody()))

    with pytest.raises(ResidencyError, match="HTTP 500"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


@pytest.mark.parametrize(
    "network_error",
    [
        urllib.error.URLError("Connection refused"),
        TimeoutError("timed out"),
        ConnectionResetError("reset"),
    ],
    ids=["refused", "timeout", "reset"],
)
def test_network_failures_are_unreachable(urlopen, network_error):
    urlopen(network_error)

    with pytest.raises(ResidencyError, match="unreachable"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


def test_an_answer_that_is_not_json_is_a_failure(urlopen):
    urlopen(FakeHTTPResponse(b"<html>not json</html>"))

    with pytest.raises(ResidencyError, match="not JSON"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


def test_an_answer_that_is_not_utf8_is_a_failure(urlopen):
    urlopen(FakeHTTPResponse(b"\xff\xfe\x00"))

    with pytest.raises(ResidencyError, match="not JSON"):
        request_json("POST", URL, {}, timeout_seconds=1.0)


def test_a_json_list_is_not_an_object(urlopen):
    urlopen(FakeHTTPResponse(b"[1, 2]"))

    with pytest.raises(ResidencyError, match="not an object"):
        request_json("GET", URL, None, timeout_seconds=1.0)
