"""Unit tests for the captive-portal settings section."""

from core.config import (
    DEFAULT_CAPTIVE_PORTAL_ENABLED,
    DEFAULT_CAPTIVE_PORTAL_URL,
    CaptivePortalConfig,
    build_captive_portal_config,
    clear_settings_cache,
    get_settings,
)


def test_captive_portal_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CAPTIVE_PORTAL_ENABLED", raising=False)
    monkeypatch.delenv("CAPTIVE_PORTAL_URL", raising=False)
    clear_settings_cache()
    portal = get_settings().captive_portal
    assert portal == CaptivePortalConfig()
    assert portal.enabled is DEFAULT_CAPTIVE_PORTAL_ENABLED is True
    assert (
        portal.redirect_url == DEFAULT_CAPTIVE_PORTAL_URL == "http://tutorbox/alumno/"
    )


def test_captive_portal_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "false")
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", "  http://192.168.8.2/alumno/  ")
    clear_settings_cache()
    portal = get_settings().captive_portal
    assert portal.enabled is False
    assert portal.redirect_url == "http://192.168.8.2/alumno/"


def test_captive_portal_blank_url_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("CAPTIVE_PORTAL_URL", "   ")
    assert build_captive_portal_config().redirect_url == DEFAULT_CAPTIVE_PORTAL_URL


def test_captive_portal_garbage_bool_keeps_default(monkeypatch) -> None:
    monkeypatch.setenv("CAPTIVE_PORTAL_ENABLED", "maybe")
    assert build_captive_portal_config().enabled is DEFAULT_CAPTIVE_PORTAL_ENABLED
