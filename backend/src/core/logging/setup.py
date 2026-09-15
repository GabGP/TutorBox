"""Logging initialization and configuration for TutorBox."""

import logging
import os
import sys

from uvicorn.logging import AccessFormatter, ColourizedFormatter

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

_ROOT_HANDLER_MARKER = "_tutorbox_managed"


def _is_managed_handler(handler: logging.Handler) -> bool:
    """Only touch unset or Uvicorn-family formatters; leave foreign (pytest/user) alone.

    TutorBoxAccessFormatter requires 5-arg access records and crashes on normal
    log records, so it must never be applied to shared handlers (e.g. pytest's
    LogCaptureHandler attached to both root and uvicorn loggers).
    """
    formatter = handler.formatter
    return formatter is None or isinstance(
        formatter, (ColourizedFormatter, AccessFormatter)
    )


def setup_logging(
    log_level: str | None = None,
    suppress_probes: bool | None = None,
    use_colors: bool | None = None,
) -> None:
    """Configures application and Uvicorn loggers with unified timestamps and colors."""
    raw_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, raw_level.upper(), logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

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

    # Configure root logger without hijacking foreign handlers (e.g. pytest caplog).
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    owned_handlers = [
        h for h in root_logger.handlers if getattr(h, _ROOT_HANDLER_MARKER, False)
    ]
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(app_formatter)
        setattr(handler, _ROOT_HANDLER_MARKER, True)
        root_logger.addHandler(handler)
    elif owned_handlers:
        for handler in owned_handlers:
            handler.setFormatter(app_formatter)

    # Configure Uvicorn server loggers (skip foreign handlers like pytest's).
    for logger_name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.setLevel(numeric_level)
        for h in uv_logger.handlers:
            if _is_managed_handler(h):
                h.setFormatter(server_formatter)

    # Configure Uvicorn access logger (skip foreign handlers like pytest's).
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(numeric_level)
    for h in access_logger.handlers:
        if not _is_managed_handler(h):
            continue
        h.setFormatter(access_formatter)
        existing_filters = [f for f in h.filters if isinstance(f, ProbeFilter)]
        if should_suppress_probes and not existing_filters:
            h.addFilter(ProbeFilter())
        elif not should_suppress_probes and existing_filters:
            for f in existing_filters:
                h.removeFilter(f)

    # Quiet noisy third-party libraries when not debugging; restore on DEBUG
    # so INFO -> DEBUG transitions don't leave them stuck at WARNING.
    for noisy_name in QUIET_THIRD_PARTY_LOGGERS:
        logging.getLogger(noisy_name).setLevel(
            logging.WARNING if numeric_level > logging.DEBUG else numeric_level
        )
