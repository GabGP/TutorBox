"""Runs blocking work in the threadpool and flags it once the client disconnects."""

import asyncio
import contextlib
import threading
from collections.abc import Callable
from typing import Protocol, TypeVar

from starlette.concurrency import run_in_threadpool

ResultType = TypeVar("ResultType")

DISCONNECT_POLL_SECONDS: float = 0.5


class DisconnectAware(Protocol):
    """The part of a Starlette request the watcher needs."""

    async def is_disconnected(self) -> bool: ...


async def _flag_when_disconnected(
    request: DisconnectAware, client_gone: threading.Event
) -> None:
    """Polls the connection and sets `client_gone` when the client leaves."""
    while not await request.is_disconnected():
        await asyncio.sleep(DISCONNECT_POLL_SECONDS)
    client_gone.set()


async def run_until_disconnected(
    request: DisconnectAware,
    blocking_work: Callable[[Callable[[], bool]], ResultType],
) -> ResultType:
    """Runs `blocking_work(client_has_left)` off the event loop.

    `client_has_left` turns True once the client closes the connection (for
    example the teacher pressed Detener), so the work can stop between steps
    instead of finishing a result nobody will read.
    """
    client_gone = threading.Event()
    watcher = asyncio.create_task(_flag_when_disconnected(request, client_gone))
    try:
        return await run_in_threadpool(blocking_work, client_gone.is_set)
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await watcher
