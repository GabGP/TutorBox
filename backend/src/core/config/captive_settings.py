"""Builder for the captive-portal settings section (see api/captive.py)."""

import os

from core.config.constants import (
    DEFAULT_CAPTIVE_PORTAL_ENABLED,
    DEFAULT_CAPTIVE_PORTAL_URL,
)
from core.config.models import CaptivePortalConfig
from core.config.parsers import parse_bool

__all__ = ["build_captive_portal_config"]


def build_captive_portal_config() -> CaptivePortalConfig:
    """Reads CAPTIVE_PORTAL_* from the environment; blank URL keeps the default."""
    raw_url = (os.environ.get("CAPTIVE_PORTAL_URL") or "").strip()
    return CaptivePortalConfig(
        enabled=parse_bool("CAPTIVE_PORTAL_ENABLED", DEFAULT_CAPTIVE_PORTAL_ENABLED),
        redirect_url=raw_url or DEFAULT_CAPTIVE_PORTAL_URL,
    )
