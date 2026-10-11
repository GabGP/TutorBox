"""The presence store: when each phone and clicker was last heard from."""

from api.presence.store import FORGET_SECONDS, PresenceStore, Sighting
from tests.api.presence.presence_support import FakeClock

DEVICE_ID = "ESP32-A4CF12"


def test_a_phone_is_found_with_the_seconds_since_its_last_beat():
    clock = FakeClock()
    store = PresenceStore(clock=clock)

    store.phone_seen(7)
    clock.advance(4)

    assert store.phone(7) == Sighting(seconds_ago=4)


def test_a_phone_or_clicker_never_heard_from_is_none():
    store = PresenceStore(clock=FakeClock())

    assert store.phone(7) is None
    assert store.clicker(DEVICE_ID) is None


def test_a_clicker_is_found_with_the_vitals_it_sent():
    clock = FakeClock()
    store = PresenceStore(clock=clock)

    store.clicker_seen(DEVICE_ID, rssi=-58, battery_pct=88)
    clock.advance(5)

    assert store.clicker(DEVICE_ID) == Sighting(seconds_ago=5, rssi=-58, battery_pct=88)


def test_the_next_beat_of_a_clicker_replaces_its_vitals():
    clock = FakeClock()
    store = PresenceStore(clock=clock)
    store.clicker_seen(DEVICE_ID, rssi=-58, battery_pct=88)

    store.clicker_seen(DEVICE_ID, rssi=-70, battery_pct=None)

    assert store.clicker(DEVICE_ID) == Sighting(
        seconds_ago=0, rssi=-70, battery_pct=None
    )


def test_phones_and_clickers_are_kept_apart():
    store = PresenceStore(clock=FakeClock())

    store.clicker_seen("7", rssi=-50, battery_pct=90)
    store.phone_seen(9)

    assert store.phone(7) is None
    assert store.clicker("9") is None
    assert store.clicker("7") == Sighting(seconds_ago=0, rssi=-50, battery_pct=90)
    assert store.phone(9) == Sighting(seconds_ago=0)


def test_an_entry_is_forgotten_once_thirty_minutes_have_passed():
    clock = FakeClock()
    store = PresenceStore(clock=clock)
    store.phone_seen(7)
    store.clicker_seen(DEVICE_ID, rssi=-60, battery_pct=80)

    clock.advance(FORGET_SECONDS - 1)
    assert store.phone(7) == Sighting(seconds_ago=1799)
    assert store.clicker(DEVICE_ID) == Sighting(
        seconds_ago=1799, rssi=-60, battery_pct=80
    )

    clock.advance(1)
    assert store.phone(7) is None
    assert store.clicker(DEVICE_ID) is None


def test_a_beat_forgets_the_other_entries_that_have_gone_stale():
    clock = FakeClock()
    store = PresenceStore(clock=clock)
    store.phone_seen(7)
    clock.advance(FORGET_SECONDS)

    store.phone_seen(8)

    assert store.phone(7) is None
    assert store.phone(8) == Sighting(seconds_ago=0)


def test_the_forget_time_is_a_constructor_argument():
    clock = FakeClock()
    store = PresenceStore(forget_seconds=60, clock=clock)
    store.phone_seen(7)

    clock.advance(59)
    assert store.phone(7) == Sighting(seconds_ago=59)

    clock.advance(1)
    assert store.phone(7) is None
