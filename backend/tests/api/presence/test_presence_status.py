"""The presence rules: connection status and signal level, at their edges."""

import pytest

from api.presence.status import best_status, connection_status, signal_level
from api.presence.store import Sighting


def test_no_sighting_means_absent():
    assert connection_status(None) == "absent"


@pytest.mark.parametrize(
    ("seconds_ago", "expected"),
    [
        (0, "online"),
        (15, "online"),
        (16, "dropped"),
        (1799, "dropped"),
    ],
)
def test_a_beat_within_fifteen_seconds_is_online_and_older_ones_are_dropped(
    seconds_ago, expected
):
    assert connection_status(Sighting(seconds_ago=seconds_ago)) == expected


@pytest.mark.parametrize(
    ("rssi", "expected"),
    [
        (None, None),
        (-40, "good"),
        (-65, "good"),
        (-66, "fair"),
        (-75, "fair"),
        (-76, "weak"),
        (-120, "weak"),
    ],
)
def test_signal_levels_change_at_minus_65_and_minus_75_dbm(rssi, expected):
    assert signal_level(rssi) == expected


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((), "absent"),
        (("absent",), "absent"),
        (("absent", "dropped"), "dropped"),
        (("dropped", "online", "absent"), "online"),
        (("absent", "absent"), "absent"),
    ],
)
def test_the_best_status_is_online_then_dropped_then_absent(statuses, expected):
    assert best_status(*statuses) == expected
