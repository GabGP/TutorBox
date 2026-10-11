"""The process-wide presence store, built on first use.

It is a FastAPI dependency, so tests can swap in a store on a fake clock.
"""

from functools import lru_cache

from api.presence.store import PresenceStore

__all__ = ["get_presence_store"]


@lru_cache(maxsize=1)
def get_presence_store() -> PresenceStore:
    return PresenceStore()
