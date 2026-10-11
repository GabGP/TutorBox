"""When each phone and clicker in the class was last heard from, kept in memory.

Single process, like the tutor roster and the quiz's live state. A restart empties it,
and it fills again within seconds: every client beats every 5 seconds. An entry not
heard from for 30 minutes is forgotten, so the memory stays bounded.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

__all__ = ["FORGET_SECONDS", "PresenceStore", "Sighting"]

FORGET_SECONDS = 1800.0

KeyType = TypeVar("KeyType", int, str)


@dataclass(frozen=True)
class Sighting:
    """One phone or clicker, as the lobby sees it at this moment."""

    seconds_ago: int
    # Vitals are only kept for clickers; a phone's sighting has none.
    rssi: int | None = None
    battery_pct: int | None = None


@dataclass(frozen=True)
class _Beat:
    last_seen: float
    rssi: int | None = None
    battery_pct: int | None = None


class PresenceStore:
    def __init__(
        self,
        forget_seconds: float = FORGET_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._forget_seconds = forget_seconds
        self._clock = clock
        self._phones: dict[int, _Beat] = {}
        self._clickers: dict[str, _Beat] = {}
        self._lock = threading.Lock()

    def phone_seen(self, user_id: int) -> None:
        """A student's phone sent a heartbeat."""
        with self._lock:
            now = self._clock()
            self._forget_stale(now)
            self._phones[user_id] = _Beat(last_seen=now)

    def clicker_seen(
        self, device_id: str, rssi: int | None, battery_pct: int | None
    ) -> None:
        """A clicker sent a heartbeat; its vitals replace the ones it sent before."""
        with self._lock:
            now = self._clock()
            self._forget_stale(now)
            self._clickers[device_id] = _Beat(
                last_seen=now, rssi=rssi, battery_pct=battery_pct
            )

    def phone(self, user_id: int) -> Sighting | None:
        """The student's phone, or None when it was never heard from or is forgotten."""
        with self._lock:
            return self._fresh_sighting(self._phones, user_id, self._clock())

    def clicker(self, device_id: str) -> Sighting | None:
        """The clicker, or None when it was never heard from or is forgotten."""
        with self._lock:
            return self._fresh_sighting(self._clickers, device_id, self._clock())

    def _is_stale(self, beat: _Beat, now: float) -> bool:
        return now - beat.last_seen >= self._forget_seconds

    def _fresh_sighting(
        self, beats: dict[KeyType, _Beat], key: KeyType, now: float
    ) -> Sighting | None:
        beat = beats.get(key)
        if beat is None:
            return None
        if self._is_stale(beat, now):
            del beats[key]
            return None
        return Sighting(
            seconds_ago=int(now - beat.last_seen),
            rssi=beat.rssi,
            battery_pct=beat.battery_pct,
        )

    def _forget_stale(self, now: float) -> None:
        self._phones = self._without_stale(self._phones, now)
        self._clickers = self._without_stale(self._clickers, now)

    def _without_stale(
        self, beats: dict[KeyType, _Beat], now: float
    ) -> dict[KeyType, _Beat]:
        return {
            key: beat for key, beat in beats.items() if not self._is_stale(beat, now)
        }
