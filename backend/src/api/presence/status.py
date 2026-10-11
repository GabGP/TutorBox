"""Pure rules that turn a sighting into what the teacher's lobby shows.

No I/O and no clock: the store measures the age of each beat, and these functions
only compare it with the thresholds below.
"""

from typing import Literal

from api.presence.store import Sighting

__all__ = [
    "ONLINE_SECONDS",
    "ConnectionStatus",
    "SignalLevel",
    "best_status",
    "connection_status",
    "signal_level",
]

# A client beats every 5 seconds, so 15 seconds is three missed beats.
ONLINE_SECONDS = 15.0
GOOD_SIGNAL_RSSI_DBM = -65
FAIR_SIGNAL_RSSI_DBM = -75

ConnectionStatus = Literal["online", "dropped", "absent"]
SignalLevel = Literal["good", "fair", "weak"]

_STATUS_RANK: dict[ConnectionStatus, int] = {"online": 2, "dropped": 1, "absent": 0}


def connection_status(sighting: Sighting | None) -> ConnectionStatus:
    """`absent` when never heard from, `online` within 15 seconds, else `dropped`."""
    if sighting is None:
        return "absent"
    if sighting.seconds_ago <= ONLINE_SECONDS:
        return "online"
    return "dropped"


def signal_level(rssi: int | None) -> SignalLevel | None:
    """The Wi-Fi signal of a clicker in three steps; None when the RSSI is unknown."""
    if rssi is None:
        return None
    if rssi >= GOOD_SIGNAL_RSSI_DBM:
        return "good"
    if rssi >= FAIR_SIGNAL_RSSI_DBM:
        return "fair"
    return "weak"


def best_status(*statuses: ConnectionStatus) -> ConnectionStatus:
    """The most connected of the statuses: online beats dropped, dropped beats absent."""
    if not statuses:
        return "absent"
    return max(statuses, key=_STATUS_RANK.__getitem__)
