"""Unit tests for TutorBox unified logging, formatters, and filters."""

import json
import logging
import logging.config
from pathlib import Path

import pytest

from core.logging import (
    ACCESS_LOG_FORMAT,
    APP_LOG_FORMAT,
    ProbeFilter,
    TutorBoxAccessFormatter,
    TutorBoxFormatter,
    setup_logging,
)
from core.logging.setup import QUIET_THIRD_PARTY_LOGGERS

_TRACKED_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


@pytest.fixture(autouse=True)
def _preserve_logging_state():
    """Fully restores global logging state (level/handlers/propagate/formatter)."""
    root = logging.getLogger()
    saved_root_level = root.level
    saved_root_handlers = root.handlers[:]
    saved_root_state = {id(h): (h.formatter, h.filters[:]) for h in root.handlers}
    saved = {}
    for name in (*_TRACKED_LOGGERS, *QUIET_THIRD_PARTY_LOGGERS):
        logger = logging.getLogger(name)
        saved[name] = (
            logger.level,
            logger.handlers[:],
            logger.propagate,
            logger.disabled,
            {id(h): (h.formatter, h.filters[:]) for h in logger.handlers},
        )
    yield
    root.setLevel(saved_root_level)
    root.handlers = saved_root_handlers
    for handler in saved_root_handlers:
        if id(handler) in saved_root_state:
            formatter, filters = saved_root_state[id(handler)]
            handler.setFormatter(formatter)
            handler.filters = filters[:]
    for name, (level, handlers, propagate, disabled, handler_state) in saved.items():
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers = handlers
        logger.propagate = propagate
        logger.disabled = disabled
        for handler in handlers:
            if id(handler) in handler_state:
                formatter, filters = handler_state[id(handler)]
                handler.setFormatter(formatter)
                handler.filters = filters[:]


def _make_record(path: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=("192.168.4.10", "GET", path, "1.1", 200),
        exc_info=None,
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
    assert "127.0.0.1:51234       - " in formatted
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


def test_probe_filter_strips_query_and_fragment():
    """Verifies probes with query strings or fragments are still filtered."""
    probe_filter = ProbeFilter()
    assert probe_filter.filter(_make_record("/generate_204?cmode=1")) is False
    assert probe_filter.filter(_make_record("/hotspot-detect.html?x=1#y")) is False
    assert probe_filter.filter(_make_record("/alumno/?next=/maestro/")) is True


def test_probe_filter_blocks_extended_probe_paths():
    """Verifies WPAD and extensionless Android probes are filtered."""
    probe_filter = ProbeFilter()
    assert probe_filter.filter(_make_record("/wpad.dat")) is False
    assert probe_filter.filter(_make_record("/generate204")) is False


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


def test_setup_logging_restores_noisy_loggers_on_debug():
    """Verifies INFO -> DEBUG doesn't leave third-party loggers stuck at WARNING."""
    setup_logging(log_level="INFO")
    assert logging.getLogger("httpx").level == logging.WARNING
    setup_logging(log_level="DEBUG")
    assert logging.getLogger("httpx").level == logging.DEBUG


def test_setup_logging_invalid_level_falls_back_to_info():
    """Verifies unknown LOG_LEVEL strings fall back to INFO."""
    setup_logging(log_level="BOGUS_LEVEL")
    assert logging.getLogger().level == logging.INFO
    # logging.BASIC_FORMAT is a str, so getattr returns non-int -> INFO fallback.
    setup_logging(log_level="basic_format")
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_leaves_foreign_root_handlers_alone():
    """Verifies external root handlers (e.g. pytest caplog) keep their formatter."""
    root = logging.getLogger()
    foreign = logging.StreamHandler()
    sentinel = logging.Formatter("%(message)s FOREIGN")
    foreign.setFormatter(sentinel)
    root.handlers = [foreign]

    setup_logging(log_level="INFO")

    assert root.handlers == [foreign]
    assert foreign.formatter is sentinel


def test_setup_logging_leaves_foreign_uvicorn_handlers_alone():
    """Verifies shared/foreign handlers (e.g. pytest capture) never get access format."""
    foreign_formatter = logging.Formatter("%(message)s FOREIGN")
    shared = logging.StreamHandler()
    shared.setFormatter(foreign_formatter)
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = [shared]

    setup_logging(log_level="INFO", suppress_probes=True)

    assert shared.formatter is foreign_formatter
    assert not any(isinstance(f, ProbeFilter) for f in shared.filters)
    # Normal records must still format through the untouched foreign handler.
    record = logging.LogRecord(
        name="tutorbox",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello",
        args=(),
        exc_info=None,
    )
    assert "hello" in shared.format(record)


def test_setup_logging_reformats_owned_root_handler():
    """Verifies a second setup_logging call refreshes the owned root handler."""
    root = logging.getLogger()
    root.handlers = []
    setup_logging(log_level="INFO")
    assert len(root.handlers) == 1
    owned = root.handlers[0]
    setup_logging(log_level="DEBUG")
    assert root.handlers == [owned]
    assert root.level == logging.DEBUG


def test_setup_logging_creates_stream_handler_if_none_present():
    """Verifies that a stream handler is created on root logger if handlers list was empty."""
    root = logging.getLogger()
    root.handlers = []
    setup_logging(log_level="INFO")
    assert len(root.handlers) >= 1


def test_logging_config_uses_tutorbox_formatters():
    """Verifies logging_config.json loads and uses TutorBox formatter classes."""
    config_path = Path(__file__).resolve().parents[3] / "logging_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    logging.config.dictConfig(config)

    uv_error = logging.getLogger("uvicorn.error")
    assert uv_error.handlers, "uvicorn.error must have handlers from dictConfig"
    assert isinstance(uv_error.handlers[0].formatter, TutorBoxFormatter)

    access_logger = logging.getLogger("uvicorn.access")
    assert access_logger.handlers
    assert isinstance(access_logger.handlers[0].formatter, TutorBoxAccessFormatter)
