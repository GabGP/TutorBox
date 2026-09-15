"""Unit tests for TutorBox unified logging, formatters, and filters."""

import logging

from core.logging import (
    ACCESS_LOG_FORMAT,
    APP_LOG_FORMAT,
    ProbeFilter,
    TutorBoxAccessFormatter,
    TutorBoxFormatter,
    setup_logging,
)


def test_tutorbox_formatter_includes_timestamp_and_levelprefix():
    """Verifies that TutorBoxFormatter outputs timestamp, levelprefix, and module name."""
    formatter = TutorBoxFormatter(fmt=APP_LOG_FORMAT, use_colors=False)
    record = logging.LogRecord(
        name="core.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Sample log event",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "INFO:    " in formatted
    assert "[core.test]" in formatted
    assert "Sample log event" in formatted


def test_tutorbox_access_formatter_includes_timestamp_and_request_line():
    """Verifies that TutorBoxAccessFormatter formats HTTP access records correctly."""
    formatter = TutorBoxAccessFormatter(fmt=ACCESS_LOG_FORMAT, use_colors=False)
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:51234", "GET", "/api/v1/health", "1.1", 200),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "127.0.0.1:51234" in formatted
    assert "GET /api/v1/health HTTP/1.1" in formatted
    assert "200 OK" in formatted


def test_probe_filter_blocks_captive_probes():
    """Verifies that ProbeFilter drops captive portal probes from access logs."""
    probe_filter = ProbeFilter()
    blocked_record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=("192.168.4.10", "GET", "/generate_204", "1.1", 204),
        exc_info=None,
    )
    assert probe_filter.filter(blocked_record) is False

    allowed_record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=("192.168.4.10", "GET", "/alumno/", "1.1", 200),
        exc_info=None,
    )
    assert probe_filter.filter(allowed_record) is True


def test_probe_filter_allows_malformed_or_non_http_records():
    """Verifies ProbeFilter safely allows records with incomplete args."""
    probe_filter = ProbeFilter()
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Generic message",
        args=(),
        exc_info=None,
    )
    assert probe_filter.filter(record) is True


def test_setup_logging_configures_loggers_and_levels(monkeypatch):
    """Verifies setup_logging sets root, uvicorn, and third-party levels."""
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_SUPPRESS_PROBES", raising=False)

    uv_logger = logging.getLogger("uvicorn")
    uv_logger.handlers = [logging.StreamHandler()]

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = [logging.StreamHandler()]

    setup_logging(log_level="DEBUG", suppress_probes=True)

    assert logging.getLogger().level == logging.DEBUG
    assert uv_logger.level == logging.DEBUG
    assert access_logger.level == logging.DEBUG
    assert any(isinstance(f, ProbeFilter) for f in access_logger.handlers[0].filters)


def test_setup_logging_removes_probe_filter_when_disabled():
    """Verifies setup_logging cleans up existing ProbeFilter when suppress_probes is False."""
    access_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.addFilter(ProbeFilter())
    access_logger.handlers = [handler]

    setup_logging(log_level="INFO", suppress_probes=False)
    assert not any(
        isinstance(f, ProbeFilter) for f in access_logger.handlers[0].filters
    )


def test_setup_logging_quiets_noisy_loggers_when_info():
    """Verifies that third-party noisy libraries are quieted when not debugging."""
    setup_logging(log_level="INFO")
    assert logging.getLogger("watchfiles.main").level == logging.WARNING
    assert logging.getLogger("multipart").level == logging.WARNING


def test_setup_logging_creates_stream_handler_if_none_present():
    """Verifies that a stream handler is created on root logger if handlers list was empty."""
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    try:
        root.handlers = []
        setup_logging(log_level="INFO")
        assert len(root.handlers) >= 1
    finally:
        root.handlers = saved_handlers
