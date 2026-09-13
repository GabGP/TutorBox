"""Captive-portal probes and the foreign-host walled garden (src/api/captive.py)."""

import pytest
from fastapi.testclient import TestClient

from api.captive import PROBE_PATHS, RESERVED_PREFIXES
from core.config import clear_settings_cache
from main import PILAS_MOUNTS

STUDENT_URL = "http://tutorbox/alumno/"
FOREIGN = {"host": "captive.apple.com"}
APPLIANCE = {"host": "192.168.8.2"}


@pytest.fixture
def captive_env(monkeypatch):
    """Pins the portal settings so a developer's .env cannot leak into assertions."""
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "true")
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", STUDENT_URL)
    clear_settings_cache()
    yield
    clear_settings_cache()


def _get(client: TestClient, path: str, host: str):
    return client.get(path, headers={"host": host}, follow_redirects=False)


@pytest.mark.parametrize("path", PROBE_PATHS)
def test_probe_paths_redirect_to_student_page(captive_env, temp_db, client, path):
    for host in ("connectivitycheck.gstatic.com", "192.168.8.2", "localhost"):
        resp = _get(client, path, host)
        assert resp.status_code == 302, (path, host)
        assert resp.headers["location"] == STUDENT_URL
        assert resp.headers["cache-control"] == "no-store"


def test_probe_paths_answer_head(captive_env, temp_db, client):
    resp = client.head("/generate_204", headers=FOREIGN, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == STUDENT_URL
    assert resp.content == b""


def test_probe_paths_hidden_from_openapi(captive_env, temp_db, client):
    paths = client.get("/openapi.json").json()["paths"]
    assert not any(path in paths for path in PROBE_PATHS)


def test_unknown_path_on_foreign_host_redirects(captive_env, temp_db, client):
    for host in (
        "www.msftconnecttest.com",
        "captive.apple.com:8080",
        "testserver",
        "8.8.8.8",
    ):
        resp = _get(client, "/some/page", host)
        assert resp.status_code == 302, host
        assert resp.headers["location"] == STUDENT_URL
        assert resp.headers["cache-control"] == "no-store"


def test_unknown_path_on_appliance_host_keeps_json_404(captive_env, temp_db, client):
    for host in (
        "192.168.8.2",
        "192.168.8.2:8000",
        "localhost",
        "tutorbox",
        "[fd00::2]:80",
    ):
        resp = _get(client, "/some/page", host)
        assert resp.status_code == 404, host
        assert resp.json() == {"detail": "Not Found"}


def test_root_on_foreign_host_redirects_to_canonical_url(captive_env, temp_db, client):
    resp = _get(client, "/", "connectivity-check.ubuntu.com")
    assert resp.status_code == 302
    assert resp.headers["location"] == STUDENT_URL
    resp = _get(client, "/", "localhost")
    assert resp.status_code == 307
    assert resp.headers["location"] == "/alumno/"


def test_api_paths_never_redirect(captive_env, staff_db, client):
    assert _get(client, "/api/v1/nope", "captive.apple.com").json() == {
        "detail": "Not Found"
    }
    resp = _get(client, "/api/v1/session/does-not-exist", "captive.apple.com")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Session 'does-not-exist' not found."}
    resp = client.post("/whatever", headers=FOREIGN, follow_redirects=False)
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}
    assert _get(client, "/health", "captive.apple.com").status_code == 200


def test_reserved_prefixes_keep_asset_404(captive_env, temp_db, client):
    for path in ("/static/missing.css", "/alumno/missing.js", "/maestro/x.png"):
        resp = _get(client, path, "captive.apple.com")
        assert resp.status_code == 404, path
        assert resp.json() == {"detail": "Not Found"}


def test_reserved_prefixes_cover_pilas_mounts():
    for mount in PILAS_MOUNTS:
        assert f"/{mount}/" in RESERVED_PREFIXES
    assert "/api/" in RESERVED_PREFIXES
    assert "/health" in RESERVED_PREFIXES


def test_disabled_portal_restores_plain_404(captive_env, monkeypatch, temp_db, client):
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "false")
    clear_settings_cache()
    for path in ("/generate_204", "/some/page"):
        resp = _get(client, path, "captive.apple.com")
        assert resp.status_code == 404, path
        assert resp.json() == {"detail": "Not Found"}
    resp = _get(client, "/", "captive.apple.com")
    assert resp.status_code == 307
    assert resp.headers["location"] == "/alumno/"


def test_redirect_url_is_configurable(captive_env, monkeypatch, temp_db, client):
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", "http://192.168.8.2/alumno/")
    clear_settings_cache()
    resp = _get(client, "/hotspot-detect.html", "captive.apple.com")
    assert resp.headers["location"] == "http://192.168.8.2/alumno/"
    # The redirect target's own host is the appliance, never a walled-garden hit.
    resp = _get(client, "/some/page", "192.168.8.2")
    assert resp.status_code == 404
    resp = _get(client, "/some/page", "tutorbox")
    assert resp.status_code == 302
