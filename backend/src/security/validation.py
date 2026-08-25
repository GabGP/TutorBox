"""Validation constants and regex patterns for authentication and user fields."""

import re

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 32
USERNAME_PATTERN = r"^[A-Za-z0-9_.-]{3,32}$"

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 8
PIN_PATTERN = r"^\d{4,8}$"

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
UUID_RE = re.compile(UUID_PATTERN, re.IGNORECASE)

ALLOWED_ROLES = frozenset({"student", "teacher", "admin"})
