"""HTTP(S) opener that gets past a network whose IPv6 route is broken.

urllib connects to each resolved address in turn and waits the whole request
timeout (60 s) on every one. On a network that announces IPv6 but does not route
it, every Hugging Face download then stalls for minutes before IPv4 is tried.
Here each address gets a short connect timeout, IPv6 and IPv4 addresses take
turns, and once an IPv6 connect fails the rest of the run tries IPv4 first.
"""

import http.client
import socket
import urllib.request
from typing import Any

CONNECT_TIMEOUT_SECONDS = 5.0


class _AddressPreference:
    """Remembers, for this process, that IPv6 connects have failed."""

    ipv6_failed = False


def order_addresses(addresses: list[Any]) -> list[Any]:
    """Interleaves the two address families, IPv4 first once IPv6 has failed."""
    ipv6 = [entry for entry in addresses if entry[0] == socket.AF_INET6]
    others = [entry for entry in addresses if entry[0] != socket.AF_INET6]
    if not ipv6 or not others:
        return list(addresses)
    first_family_is_ipv6 = (
        addresses[0][0] == socket.AF_INET6 and not _AddressPreference.ipv6_failed
    )
    first, second = (ipv6, others) if first_family_is_ipv6 else (others, ipv6)
    ordered: list[Any] = []
    for index in range(max(len(first), len(second))):
        ordered.extend(group[index] for group in (first, second) if index < len(group))
    return ordered


def create_connection(
    address: tuple[str, int],
    timeout: float | None = None,
    source_address: tuple[str, int] | None = None,
) -> socket.socket:
    """Connects to the first address that answers within the connect timeout."""
    host, port = address
    resolved = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    last_error: OSError = OSError(f"No address found for {host}")
    for family, sock_type, proto, _, sockaddr in order_addresses(resolved):
        sock = socket.socket(family, sock_type, proto)
        try:
            sock.settimeout(CONNECT_TIMEOUT_SECONDS)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
        except OSError as error:
            sock.close()
            last_error = error
            if family == socket.AF_INET6:
                _AddressPreference.ipv6_failed = True
            continue
        sock.settimeout(timeout)
        return sock
    raise last_error


class _FallbackHTTPConnection(http.client.HTTPConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._create_connection = create_connection


class _FallbackHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._create_connection = create_connection


class _FallbackHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(_FallbackHTTPConnection, req)


class _FallbackHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        # HTTPSHandler keeps its SSL context in _context (undeclared in typeshed).
        context = getattr(self, "_context", None)
        return self.do_open(_FallbackHTTPSConnection, req, context=context)


_OPENER = urllib.request.build_opener(_FallbackHTTPHandler, _FallbackHTTPSHandler)


def open_url(request: urllib.request.Request, timeout: float) -> Any:
    """urlopen() with the fallback connections; follows redirects the same way."""
    return _OPENER.open(request, timeout=timeout)
