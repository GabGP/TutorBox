"""Configuration constants and environment variable resolvers for rate limiters."""

import config
from config import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    get_settings,
)

DEFAULT_MAX_ATTEMPTS: int = DEFAULT_AUTH_MAX_ATTEMPTS
DEFAULT_LOCKOUT_DURATION_SECONDS: int = DEFAULT_AUTH_LOCKOUT_SECONDS
DEFAULT_MAX_TRACKED_KEYS: int = DEFAULT_AUTH_MAX_TRACKED_KEYS

DEFAULT_SIGNUP_MAX_EVENTS: int = config.DEFAULT_SIGNUP_MAX_EVENTS
DEFAULT_SIGNUP_WINDOW_SECONDS: int = config.DEFAULT_SIGNUP_WINDOW_SECONDS


def get_auth_max_attempts() -> int:
    return get_settings(reload=True).security.auth_max_attempts


def get_auth_lockout_seconds() -> int:
    return get_settings(reload=True).security.auth_lockout_seconds


def get_auth_max_tracked_keys() -> int:
    return get_settings(reload=True).security.auth_max_tracked_keys


def get_signup_max_events() -> int:
    return get_settings(reload=True).security.signup_max_events


def get_signup_window_seconds() -> int:
    return get_settings(reload=True).security.signup_window_seconds
