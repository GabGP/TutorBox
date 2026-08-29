"""Validation constants, regex patterns, and reusable Pydantic field types."""

import re
from typing import Annotated

from pydantic import Field

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 32
USERNAME_PATTERN = r"^[A-Za-z0-9_.-]{3,32}$"

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 8
PIN_PATTERN = r"^\d{4,8}$"

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
UUID_RE = re.compile(UUID_PATTERN, re.IGNORECASE)

ROLE_PATTERN = r"^(student|teacher|admin)$"
ALLOWED_ROLES = frozenset({"student", "teacher", "admin"})

# Reusable Pydantic annotated field types
UsernameField = Annotated[
    str,
    Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        examples=["student1"],
    ),
]

PinField = Annotated[
    str,
    Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
        examples=["1234"],
    ),
]

RoleField = Annotated[
    str,
    Field(
        "student",
        pattern=ROLE_PATTERN,
        examples=["student"],
    ),
]

DEVICE_ID_MIN_LENGTH = 1
DEVICE_ID_MAX_LENGTH = 32
DEVICE_ID_PATTERN = r"^[A-Za-z0-9_.-]{1,32}$"

DeviceIdField = Annotated[
    str,
    Field(
        ...,
        min_length=DEVICE_ID_MIN_LENGTH,
        max_length=DEVICE_ID_MAX_LENGTH,
        pattern=DEVICE_ID_PATTERN,
        examples=["1", "ESP32_01"],
    ),
]
