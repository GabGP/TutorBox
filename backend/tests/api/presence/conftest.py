"""Presence tests share one store on a fake clock, swapped in for the process-wide one."""

from collections.abc import Iterator

import pytest

from api.presence.service import get_presence_store
from api.presence.store import PresenceStore
from src.main import app
from tests.api.presence.presence_support import FakeClock


@pytest.fixture
def presence_clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def presence_store(presence_clock: FakeClock) -> Iterator[PresenceStore]:
    """The store the app uses during the test, reading the fake clock."""
    store = PresenceStore(clock=presence_clock)
    app.dependency_overrides[get_presence_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_presence_store, None)
