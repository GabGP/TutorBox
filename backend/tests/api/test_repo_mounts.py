"""Static apps checked into the repo (REPO_MOUNTS in src/main.py): Primero app and APK downloads."""

import mimetypes

import pytest

from api.captive import RESERVED_PREFIXES
from core.config import clear_settings_cache
from main import REPO_MOUNTS


@pytest.fixture
def captive_env(monkeypatch):
    """Pins portal settings so developer .env cannot leak into assertions."""
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "true")
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", "http://tutorbox/alumno/")
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_primero_app_is_served_with_relative_assets(temp_db, client):
    resp = client.get("/tareas/primero/")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # Relative paths are what let the same files work here, on Netlify and inside the APK.
    assert 'src="js/app.js"' in resp.text
    assert client.get("/tareas/primero/js/app.js").status_code == 200
    assert client.get("/tareas/primero/fonts/nunito-latin.woff2").status_code == 200


def test_downloads_page_is_served(temp_db, client):
    resp = client.get("/descargas/")

    assert resp.status_code == 200
    assert 'href="primero.apk"' in resp.text


def test_apk_is_served_as_an_android_package():
    # main.py registers the type; without it Android saves the file as "primero.apk.txt".
    assert mimetypes.guess_type("primero.apk")[0] == (
        "application/vnd.android.package-archive"
    )


def test_repo_mount_directories_exist():
    for name, directory in REPO_MOUNTS.items():
        assert (directory / "index.html").is_file(), name


def test_missing_file_under_repo_mount_stays_404_on_foreign_host(
    captive_env, temp_db, client
):
    for path in ("/tareas/primero/js/nope.js", "/descargas/nope.apk"):
        resp = client.get(
            path, headers={"host": "captive.apple.com"}, follow_redirects=False
        )
        assert resp.status_code == 404, path
        assert resp.json() == {"detail": "Not Found"}


def test_repo_mounts_are_reserved_from_captive_redirects():
    for name in REPO_MOUNTS:
        prefix = f"/{name.split('/')[0]}/"
        assert prefix in RESERVED_PREFIXES, name
