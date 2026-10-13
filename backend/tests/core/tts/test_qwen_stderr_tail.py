"""Unit tests for the background stderr tail of the Qwen daemon client."""

import io
import os
import time
from unittest.mock import MagicMock

import pytest

from core.tts.engines.qwen.stderr_tail import StderrTail


def _wait_until_tail_shows(tail: StderrTail, expected_text: str) -> None:
    """Polls without blocking until the reader thread has stored the expected text."""
    deadline = time.monotonic() + 5.0
    while expected_text not in tail.text(wait_seconds=0.0):
        assert time.monotonic() < deadline, "reader thread never stored the line"
        time.sleep(0.01)


def test_text_returns_all_lines_below_the_limit():
    tail = StderrTail(io.StringIO("first warning\nsecond warning\n"), max_lines=5)
    assert tail.text() == "first warning\nsecond warning"


def test_text_keeps_only_the_last_lines_above_the_limit():
    lines = "".join(f"line {number}\n" for number in range(1, 8))
    tail = StderrTail(io.StringIO(lines), max_lines=3)
    assert tail.text() == "line 5\nline 6\nline 7"


def test_text_is_empty_for_a_missing_stream():
    assert StderrTail(None).text() == ""


@pytest.mark.parametrize(
    "read_error",
    [OSError("Bad file descriptor"), ValueError("I/O operation on closed file.")],
)
def test_reader_ends_quietly_when_the_pipe_breaks(read_error):
    broken_stream = MagicMock()
    broken_stream.readline.side_effect = ["kept line\n", read_error]
    tail = StderrTail(broken_stream)
    assert tail.text() == "kept line"
    # The reader stops at the error and never calls readline again.
    assert broken_stream.readline.call_count == 2


def test_text_returns_within_the_wait_when_the_stream_never_ends():
    """A child that keeps its stderr open must not hold text() past the wait."""
    read_descriptor, write_descriptor = os.pipe()
    read_stream = os.fdopen(read_descriptor, "r", encoding="utf-8")
    write_stream = os.fdopen(write_descriptor, "w", encoding="utf-8")
    try:
        tail = StderrTail(read_stream)
        write_stream.write("still running\n")
        write_stream.flush()
        _wait_until_tail_shows(tail, "still running")
        started_at = time.monotonic()
        text = tail.text(wait_seconds=0.05)
        elapsed_seconds = time.monotonic() - started_at
    finally:
        write_stream.close()
        read_stream.close()
    assert text == "still running"
    assert elapsed_seconds < 1.0
