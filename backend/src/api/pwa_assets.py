"""Root PWA asset aliases for installability and iOS probes.

The classroom client is mounted per folder (/maestro, /alumno, /pantalla,
/static) so /api/* keeps JSON 404s. Browsers and iOS still request PWA files
at "/": /manifest.webmanifest, /favicon.*, /icon-*, /apple-touch-icon*.png.
These aliases serve the same bytes from <client>/static/ without a new mount.
Missing files stay JSON 404 so backend tests can pin the legacy pilas client.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.config.constants import PROJECT_ROOT

router = APIRouter(include_in_schema=False)

# Root URL filename -> (file inside <client>/static/, media type).
ROOT_ASSET_MAP: dict[str, tuple[str, str]] = {
    "manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "favicon.svg": ("favicon.svg", "image/svg+xml"),
    "favicon.ico": ("favicon.svg", "image/x-icon"),
    "icon-192.svg": ("icon-192.svg", "image/svg+xml"),
    "icon-512.svg": ("icon-512.svg", "image/svg+xml"),
    "apple-touch-icon.png": ("icon-192.svg", "image/png"),
    "apple-touch-icon-precomposed.png": ("icon-192.svg", "image/png"),
}

# Exact root URLs served (used by tests and RESERVED_PREFIXES sync).
ROOT_ASSET_URLS: tuple[str, ...] = tuple(f"/{name}" for name in ROOT_ASSET_MAP)


def _client_static_dir() -> Path:
    """Mirror main.resolve_client_dir without importing main (avoid a cycle)."""
    raw = os.getenv("PWA_STATIC_DIR")
    if raw and raw.strip():
        candidate = Path(raw.strip())
        base = candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
        return (base / "static").resolve()
    return (PROJECT_ROOT / ".cache" / "pwa" / "dist" / "static").resolve()


def _serve_static_file(source_name: str, media_type: str) -> FileResponse:
    """Serve a file from the client static dir or raise JSON 404."""
    target = _client_static_dir() / source_name
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(str(target), media_type=media_type)


def _serve_apple_size(size: str) -> FileResponse:
    """Serve any /apple-touch-icon-<WxH>[-precomposed].png probe from icon-192."""
    base = size.removesuffix("-precomposed")
    if "x" not in base or not base.replace("x", "").isdigit():
        raise HTTPException(status_code=404, detail="Not Found")
    return _serve_static_file("icon-192.svg", "image/png")


def _make_endpoint(source_name: str, media_type: str):
    """Build a zero-arg endpoint closure for a mapped root asset."""

    async def _endpoint() -> FileResponse:
        return _serve_static_file(source_name, media_type)

    return _endpoint


for _url, (_source, _media) in ROOT_ASSET_MAP.items():
    router.add_api_route(
        f"/{_url}",
        endpoint=_make_endpoint(_source, _media),
        methods=["GET", "HEAD"],
    )


@router.get("/apple-touch-icon-{size}.png")
async def apple_touch_icon_sized(size: str) -> FileResponse:
    """Cover iOS size probes (/apple-touch-icon-180x180.png, 240x240, ...)."""
    return _serve_apple_size(size)
