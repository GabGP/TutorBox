"""Root PWA asset aliases served from <client>/static/ (src/api/pwa_assets.py)."""

import pytest
from fastapi.testclient import TestClient

from api.captive import RESERVED_PREFIXES
from api.pwa_assets import ROOT_ASSET_MAP, ROOT_ASSET_URLS, _client_static_dir
from core.config import clear_settings_cache

FOREIGN = {"host": "captive.apple.com"}


@pytest.fixture
def captive_env(monkeypatch):
    """Pins portal settings so developer .env cannot leak into assertions."""
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "true")
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", "http://tutorbox/alumno/")
    clear_settings_cache()
    yield
    clear_settings_cache()


def _get(client: TestClient, path: str, host: str = "captive.apple.com"):
    return client.get(path, headers={"host": host}, follow_redirects=False)


def test_root_asset_urls_stay_reserved():
    """Missing root aliases must keep JSON 404 on hijacked hosts, never redirect."""
    for prefix in ("/manifest.webmanifest", "/favicon.", "/icon-", "/apple-touch-icon"):
        assert prefix in RESERVED_PREFIXES
    for url in ROOT_ASSET_URLS:
        assert any(url.startswith(prefix) for prefix in RESERVED_PREFIXES), url
    assert set(ROOT_ASSET_URLS) == {f"/{name}" for name in ROOT_ASSET_MAP}


def test_missing_assets_stay_json_404(captive_env, temp_db, client):
    """Legacy pilas client ships no manifest: aliases 404 instead of redirecting."""
    for url in (
        "/manifest.webmanifest",
        "/favicon.svg",
        "/favicon.ico",
        "/icon-192.svg",
        "/apple-touch-icon.png",
        "/apple-touch-icon-180x180.png",
    ):
        resp = _get(client, url)
        assert resp.status_code == 404, url
        assert resp.json() == {"detail": "Not Found"}


def test_invalid_apple_size_is_404(captive_env, temp_db, client):
    """Non-numeric apple-touch-icon probes must not serve the fallback icon."""
    resp = _get(client, "/apple-touch-icon-abc.png")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}


def test_serves_files_from_static_dir(
    monkeypatch, captive_env, temp_db, client, tmp_path
):
    """Aliases serve <client>/static/ bytes with the mapped media type."""
    static_dir = tmp_path / "client" / "static"
    static_dir.mkdir(parents=True)
    (static_dir / "manifest.webmanifest").write_text(
        '{"name":"TutorBox"}', encoding="utf-8"
    )
    (static_dir / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    (static_dir / "icon-192.svg").write_text("<svg>192</svg>", encoding="utf-8")
    (static_dir / "icon-512.svg").write_text("<svg>512</svg>", encoding="utf-8")
    monkeypatch.setenv("PWA_STATIC_DIR", str(tmp_path / "client"))

    cases = {
        "/manifest.webmanifest": ("application/manifest+json", "TutorBox"),
        "/favicon.svg": ("image/svg+xml", "<svg>"),
        "/favicon.ico": ("image/x-icon", "<svg>"),
        "/icon-192.svg": ("image/svg+xml", "192"),
        "/icon-512.svg": ("image/svg+xml", "512"),
        "/apple-touch-icon.png": ("image/png", "192"),
        "/apple-touch-icon-precomposed.png": ("image/png", "192"),
        "/apple-touch-icon-180x180.png": ("image/png", "192"),
        "/apple-touch-icon-240x240-precomposed.png": ("image/png", "192"),
    }
    for url, (media, snippet) in cases.items():
        resp = _get(client, url, host="192.168.8.2")
        assert resp.status_code == 200, url
        assert resp.headers["content-type"].startswith(media), url
        assert snippet in resp.text, url


def test_client_static_dir_resolution(monkeypatch, tmp_path):
    """Covers default, empty, relative, and absolute PWA_STATIC_DIR branches."""
    monkeypatch.delenv("PWA_STATIC_DIR", raising=False)
    assert _client_static_dir().parts[-3:] == ("pwa", "dist", "static")

    monkeypatch.setenv("PWA_STATIC_DIR", "   ")
    assert _client_static_dir().parts[-3:] == ("pwa", "dist", "static")

    monkeypatch.setenv("PWA_STATIC_DIR", "pwa/pilas")
    resolved = _client_static_dir()
    assert resolved.name == "static"
    assert resolved.parts[-2] == "pilas"

    absolute = tmp_path / "abs-client"
    (absolute / "static").mkdir(parents=True)
    monkeypatch.setenv("PWA_STATIC_DIR", str(absolute))
    assert _client_static_dir() == absolute.resolve() / "static"


def test_root_assets_hidden_from_openapi(captive_env, temp_db, client):
    """Alias routes must not pollute the Swagger surface."""
    paths = client.get("/openapi.json").json()["paths"]
    for url in list(ROOT_ASSET_URLS) + ["/apple-touch-icon-{size}.png"]:
        assert url not in paths


def test_head_method_serves_headers(
    monkeypatch, captive_env, temp_db, client, tmp_path
):
    """HEAD probes (iOS/Captive portal) return headers without a body."""
    static_dir = tmp_path / "head-client" / "static"
    static_dir.mkdir(parents=True)
    (static_dir / "manifest.webmanifest").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("PWA_STATIC_DIR", str(tmp_path / "head-client"))
    resp = client.head("/manifest.webmanifest", headers=FOREIGN, follow_redirects=False)
    assert resp.status_code == 200
    assert resp.content == b""
