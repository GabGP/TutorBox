"""Logging initialization and configuration for TutorBox."""

import logging
import os
import sys

from core.logging.filters import ProbeFilter
from core.logging.formatter import (
    ACCESS_LOG_FORMAT,
    APP_LOG_FORMAT,
    DEFAULT_DATE_FORMAT,
    SERVER_LOG_FORMAT,
    TutorBoxAccessFormatter,
    TutorBoxFormatter,
)

QUIET_THIRD_PARTY_LOGGERS: tuple[str, ...] = (
    "watchfiles.main",
    "multipart",
    "urllib3",
    "asyncio",
    "httpcore",
    "httpx",
)


def setup_logging(
    log_level: str | None = None,
    suppress_probes: bool | None = None,
    use_colors: bool | None = None,
) -> None:
    """Configures application and Uvicorn loggers with unified timestamps and colors."""
    raw_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, raw_level.upper(), logging.INFO)

    should_suppress_probes = (
        suppress_probes
        if suppress_probes is not None
        else os.getenv("LOG_SUPPRESS_PROBES", "false").lower() in ("true", "1", "yes")
    )

    app_formatter = TutorBoxFormatter(
        fmt=APP_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        use_colors=use_colors,
    )
    server_formatter = TutorBoxFormatter(
        fmt=SERVER_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        use_colors=use_colors,
    )
    access_formatter = TutorBoxAccessFormatter(
        fmt=ACCESS_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        use_colors=use_colors,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(app_formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(app_formatter)

    # Configure Uvicorn server loggers
    for logger_name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.setLevel(numeric_level)
        for h in uv_logger.handlers:
            h.setFormatter(server_formatter)

    # Configure Uvicorn access logger
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(numeric_level)
    for h in access_logger.handlers:
        h.setFormatter(access_formatter)
        existing_filters = [f for f in h.filters if isinstance(f, ProbeFilter)]
        if should_suppress_probes and not existing_filters:
            h.addFilter(ProbeFilter())
        elif not should_suppress_probes and existing_filters:
            for f in existing_filters:
                h.removeFilter(f)

    # Quiet noisy third-party libraries when not explicitly debugging
    if numeric_level > logging.DEBUG:
        for noisy_name in QUIET_THIRD_PARTY_LOGGERS:
            logging.getLogger(noisy_name).setLevel(logging.WARNING)
