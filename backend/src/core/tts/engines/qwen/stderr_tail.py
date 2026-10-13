"""Keeps the last lines a subprocess wrote to stderr, drained on a background thread."""

from __future__ import annotations

import threading
from collections import deque
from typing import IO

__all__ = ["StderrTail"]

DEFAULT_TAIL_LINES = 40
DEFAULT_WAIT_SECONDS = 1.0


class StderrTail:
    """Drains a subprocess stderr pipe continuously and keeps only its last lines.

    A pipe that nobody reads fills up after about 64 KiB, and then the child blocks
    on its next write. Draining it on a daemon thread keeps the child running, and
    the kept lines explain a failure in error messages.
    """

    def __init__(
        self, stream: IO[str] | None, max_lines: int = DEFAULT_TAIL_LINES
    ) -> None:
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._reader_thread: threading.Thread | None = None
        if stream is not None:
            self._reader_thread = threading.Thread(
                target=self._read_lines,
                args=(stream,),
                daemon=True,
            )
            self._reader_thread.start()

    def _read_lines(self, stream: IO[str]) -> None:
        """Stores each line without its newline until end of file."""
        try:
            for line in iter(stream.readline, ""):
                with self._lock:
                    self._lines.append(line.rstrip("\n"))
        except (OSError, ValueError):
            # The pipe was closed underneath the reader; keep the lines read so far.
            return

    def text(self, wait_seconds: float = DEFAULT_WAIT_SECONDS) -> str:
        """Returns the kept lines after waiting at most wait_seconds for the reader."""
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=wait_seconds)
        with self._lock:
            return "\n".join(self._lines)
