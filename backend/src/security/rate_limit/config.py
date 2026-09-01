"""Configuration constants and environment variable resolvers for rate limiters."""

import os

DEFAULT_MAX_ATTEMPTS: int = 5
DEFAULT_LOCKOUT_DURATION_SECONDS: int = 30
DEFAULT_MAX_TRACKED_KEYS: int = 10_000

DEFAULT_SIGNUP_MAX_EVENTS: int = 30
DEFAULT_SIGNUP_WINDOW_SECONDS: int = 60


def get_auth_max_attempts() -> int:
    try:
        return int(os.getenv("AUTH_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))
    except ValueError:
        return DEFAULT_MAX_ATTEMPTS


def get_auth_lockout_seconds() -> int:
    try:
        return int(
            os.getenv("AUTH_LOCKOUT_SECONDS", str(DEFAULT_LOCKOUT_DURATION_SECONDS))
        )
    except ValueError:
        return DEFAULT_LOCKOUT_DURATION_SECONDS


def get_auth_max_tracked_keys() -> int:
    try:
        return int(os.getenv("AUTH_MAX_TRACKED_KEYS", str(DEFAULT_MAX_TRACKED_KEYS)))
    except ValueError:
        return DEFAULT_MAX_TRACKED_KEYS


def get_signup_max_events() -> int:
    try:
        return int(
            os.getenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", str(DEFAULT_SIGNUP_MAX_EVENTS))
        )
    except ValueError:
        return DEFAULT_SIGNUP_MAX_EVENTS


def get_signup_window_seconds() -> int:
    try:
        return int(
            os.getenv(
                "SIGNUP_RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_SIGNUP_WINDOW_SECONDS)
            )
        )
    except ValueError:
        return DEFAULT_SIGNUP_WINDOW_SECONDS
