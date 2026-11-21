"""Unit tests for the IPv6-tolerant opener (tools/voice_models/connect.py)."""

import socket
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from tools.voice_models import connect

V6_A = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 443, 0, 0))
V6_B = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::2", 443, 0, 0))
V4_A = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 443))
V4_B = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 443))


@pytest.fixture(autouse=True)
def fresh_preference(monkeypatch):
    """Every test starts as a new process would: IPv6 not yet known to fail."""
    monkeypatch.setattr(connect._AddressPreference, "ipv6_failed", False)


def _fake_sockets(failing_addresses: set[str]):
    """Patches socket.socket with fakes whose connect fails for the given hosts."""
    created: list[MagicMock] = []

    def make_socket(family, sock_type, proto):
        fake = MagicMock(name=f"socket-{family}")

        def connect_to(sockaddr):
            if sockaddr[0] in failing_addresses:
                raise TimeoutError(f"{sockaddr[0]} timed out")

        fake.connect.side_effect = connect_to
        created.append(fake)
        return fake

    return patch(
        "tools.voice_models.connect.socket.socket", side_effect=make_socket
    ), created


def test_order_interleaves_families_starting_with_the_resolver_choice():
    """Verifies IPv6 and IPv4 take turns, the first family being the resolver's."""
    assert connect.order_addresses([V6_A, V6_B, V4_A, V4_B]) == [V6_A, V4_A, V6_B, V4_B]
    assert connect.order_addresses([V4_A, V6_A, V6_B]) == [V4_A, V6_A, V6_B]


def test_order_puts_ipv4_first_once_ipv6_has_failed():
    """Verifies a failed IPv6 connect makes IPv4 the first family for the run."""
    connect._AddressPreference.ipv6_failed = True
    assert connect.order_addresses([V6_A, V6_B, V4_A]) == [V4_A, V6_A, V6_B]


def test_order_keeps_a_single_family_untouched():
    """Verifies a host with only one family keeps the resolver's order."""
    assert connect.order_addresses([V6_B, V6_A]) == [V6_B, V6_A]
    assert connect.order_addresses([V4_B, V4_A]) == [V4_B, V4_A]


def test_create_connection_falls_back_to_ipv4_after_an_ipv6_timeout():
    """Verifies a dead IPv6 route costs one short timeout, then IPv4 connects."""
    socket_patch, created = _fake_sockets({"2001:db8::1"})
    with (
        patch(
            "tools.voice_models.connect.socket.getaddrinfo",
            return_value=[V6_A, V4_A],
        ),
        socket_patch,
    ):
        sock = connect.create_connection(("huggingface.co", 443), timeout=60.0)

    assert sock is created[1]
    created[0].settimeout.assert_called_once_with(connect.CONNECT_TIMEOUT_SECONDS)
    created[0].close.assert_called_once()
    assert created[1].settimeout.call_args_list[-1].args == (60.0,)
    assert connect._AddressPreference.ipv6_failed is True


def test_create_connection_binds_the_source_address():
    """Verifies an explicit source address is bound before connecting."""
    socket_patch, created = _fake_sockets(set())
    with (
        patch("tools.voice_models.connect.socket.getaddrinfo", return_value=[V4_A]),
        socket_patch,
    ):
        connect.create_connection(("host", 443), 30.0, ("192.0.2.9", 0))
    created[0].bind.assert_called_once_with(("192.0.2.9", 0))


def test_create_connection_raises_the_last_error_when_nothing_answers():
    """Verifies the last connect error is raised once every address failed."""
    socket_patch, _ = _fake_sockets({"2001:db8::1", "192.0.2.1"})
    with (
        patch(
            "tools.voice_models.connect.socket.getaddrinfo",
            return_value=[V6_A, V4_A],
        ),
        socket_patch,
        pytest.raises(TimeoutError, match="192.0.2.1"),
    ):
        connect.create_connection(("host", 443), 60.0)


def test_create_connection_without_addresses_raises():
    """Verifies a name that resolves to nothing fails with an OSError."""
    with (
        patch("tools.voice_models.connect.socket.getaddrinfo", return_value=[]),
        pytest.raises(OSError, match="No address found for host"),
    ):
        connect.create_connection(("host", 443), 60.0)


def test_connections_use_the_fallback_connect():
    """Verifies both HTTP and HTTPS connections connect through create_connection."""
    http_connection = connect._FallbackHTTPConnection("example.org")
    https_connection = connect._FallbackHTTPSConnection("example.org")
    assert http_connection._create_connection is connect.create_connection
    assert https_connection._create_connection is connect.create_connection


def test_handlers_open_with_the_fallback_connections():
    """Verifies the handlers hand their own connection classes to do_open."""
    request = urllib.request.Request("https://example.org/model.onnx")
    http_handler = connect._FallbackHTTPHandler()
    https_handler = connect._FallbackHTTPSHandler()
    with (
        patch.object(http_handler, "do_open", return_value="http") as http_open,
        patch.object(https_handler, "do_open", return_value="https") as https_open,
    ):
        assert http_handler.http_open(request) == "http"
        assert https_handler.https_open(request) == "https"
    assert http_open.call_args.args == (connect._FallbackHTTPConnection, request)
    assert https_open.call_args.args == (connect._FallbackHTTPSConnection, request)
    assert https_open.call_args.kwargs == {"context": vars(https_handler)["_context"]}


def test_open_url_uses_the_fallback_opener():
    """Verifies open_url sends the request through the module's opener."""
    request = urllib.request.Request("https://example.org/model.onnx")
    with patch.object(connect, "_OPENER") as opener:
        connect.open_url(request, timeout=60.0)
    opener.open.assert_called_once_with(request, timeout=60.0)
