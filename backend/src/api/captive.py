"""Captive-portal answers: open the student page when a phone joins the classroom AP.

Phones probe a well-known HTTP URL right after associating. The classroom router
resolves every name to the appliance (dnsmasq catch-all), so those probes land here.
Answering with a redirect instead of the expected 204/"Success" makes iOS, Android
and Windows open their sign-in browser on the redirect target: the student page.
The `/api/*` surface is never redirected because ESP32 clickers treat any non-200
response as a failure.
"""

import ipaddress
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import get_settings

__all__ = [
    "PROBE_PATHS",
    "RESERVED_PREFIXES",
    "captive_not_found_handler",
    "foreign_host_redirect",
    "router",
]

# Connectivity-check paths by vendor. The Host header varies (connectivitycheck.gstatic.com,
# captive.apple.com, www.msftconnecttest.com, detectportal.firefox.com, ...) but the paths
# are stable. NetworkManager and KDE probe "/", which main.py already redirects.
PROBE_PATHS: tuple[str, ...] = (
    "/generate_204",  # Android, ChromeOS, Chrome, Xiaomi, Huawei
    "/gen_204",  # Android (www.google.com/gen_204)
    "/hotspot-detect.html",  # iOS / macOS Captive Network Assistant
    "/library/test/success.html",  # older Apple devices
    "/connecttest.txt",  # Windows 10+ NCSI
    "/ncsi.txt",  # Windows 7/8 NCSI
    "/redirect",  # Windows NCSI redirect check
    "/success.txt",  # Firefox
    "/canonical.html",  # Firefox
    "/check_network_status.txt",  # GNOME
)

# Paths whose 404s must stay JSON/plain regardless of Host: the API (clickers), the health
# probe, and the pilas mounts (a missing asset must not come back as an HTML redirect).
# Mirrors PILAS_MOUNTS in main.py (guarded by tests/api/test_captive.py).
RESERVED_PREFIXES: tuple[str, ...] = (
    "/api/",
    "/health",
    "/maestro/",
    "/alumno/",
    "/pantalla/",
    "/static/",
)


def _is_appliance_host(hostname: str | None, redirect_url: str) -> bool:
    """True when the request addressed the appliance itself rather than a hijacked name."""
    if not hostname or hostname == "localhost":
        return True
    if hostname == (urlsplit(redirect_url).hostname or "").lower():
        return True
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return True


def _redirect(url: str) -> RedirectResponse:
    # no-store: the OS must re-probe on every join instead of replaying a cached answer.
    return RedirectResponse(url, status_code=302, headers={"Cache-Control": "no-store"})


def foreign_host_redirect(request: Request) -> RedirectResponse | None:
    """Redirect to the student page when the portal is on and the Host is not ours."""
    portal = get_settings().captive_portal
    if not portal.enabled:
        return None
    if _is_appliance_host(request.url.hostname, portal.redirect_url):
        return None
    return _redirect(portal.redirect_url)


async def _probe(request: Request) -> Response:
    """Connectivity probe: redirect whatever the Host, or plain 404 when disabled."""
    portal = get_settings().captive_portal
    if not portal.enabled:
        raise HTTPException(status_code=404)
    return _redirect(portal.redirect_url)


router = APIRouter()
for _path in PROBE_PATHS:
    router.add_api_route(
        _path, _probe, methods=["GET", "HEAD"], include_in_schema=False
    )


async def captive_not_found_handler(request: Request, exc: Exception) -> Response:
    """Walled garden: unknown pages on hijacked names go to the student page."""
    if request.method in ("GET", "HEAD") and not request.url.path.startswith(
        RESERVED_PREFIXES
    ):
        redirect = foreign_host_redirect(request)
        if redirect is not None:
            return redirect
    http_exc = (
        exc
        if isinstance(exc, StarletteHTTPException)
        else StarletteHTTPException(status_code=404, detail=str(exc))
    )
    return await http_exception_handler(request, http_exc)
