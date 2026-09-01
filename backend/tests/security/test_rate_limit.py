import threading

from src.security.rate_limit import LOCKOUT_DURATION_SECONDS, InMemoryRateLimiter


def test_rate_limiter_caps_tracked_keys():
    """
    Tracked keys must never exceed max_tracked_keys, even after a flood of
    unique usernames.
    """
    limiter = InMemoryRateLimiter(max_tracked_keys=100)
    for i in range(500):
        limiter.record_failure(f"user_{i}")
    assert len(limiter._failed_attempts) <= 100


def test_rate_limiter_thread_safety_under_concurrency():
    """
    The cap invariant must survive concurrent record_failure calls from
    multiple threads (regression guard for the locking fix).
    """
    limiter = InMemoryRateLimiter(max_attempts=10**9, max_tracked_keys=100)
    errors: list[Exception] = []

    def worker(n: int) -> None:
        try:
            for i in range(250):
                limiter.record_failure(f"user_{(n * 250 + i) % 150}")
        except Exception as exc:  # noqa: BLE001 - captured and asserted below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(limiter._failed_attempts) <= 100


def test_rate_limiter_never_evicts_active_lockouts():
    """
    Actively locked-out keys must survive cap enforcement until expiry; only
    non-locked-out entries may be evicted.
    """
    limiter = InMemoryRateLimiter(max_attempts=1, max_tracked_keys=10)
    limiter.record_failure("locked_user")
    for i in range(50):
        limiter.record_failure(f"flood_{i}")
    assert limiter.is_locked_out("locked_user") is True


def test_rate_limiter_sweeps_expired_lockouts_on_write(monkeypatch):
    """
    Expired lockouts (and their counters) must be removed from internal state
    by the next recorded failure.
    """
    import time

    limiter = InMemoryRateLimiter(max_attempts=1)
    limiter.record_failure("student1")
    assert limiter.is_locked_out("student1") is True

    original_time = time.time()
    monkeypatch.setattr(
        time, "time", lambda: original_time + LOCKOUT_DURATION_SECONDS + 1
    )

    limiter.record_failure("other_user")
    assert "student1" not in limiter._lockout_until
    assert "student1" not in limiter._failed_attempts


def test_sliding_window_limiter_enforces_limit_and_expires(monkeypatch):
    """
    SlidingWindowLimiter allows events up to max_events, blocks excess,
    and expires old events after the window elapses.
    """
    import time

    from src.security.rate_limit import SlidingWindowLimiter

    limiter = SlidingWindowLimiter(max_events=2, window_seconds=10)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False  # Limit reached

    # Advance time past window
    current_time = time.time()
    monkeypatch.setattr(time, "time", lambda: current_time + 15)

    # Expired events popped, new event allowed
    assert limiter.allow() is True


def test_sliding_window_limiter_clear():
    """
    SlidingWindowLimiter.clear resets internal event queue.
    """
    from src.security.rate_limit import SlidingWindowLimiter

    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10)
    assert limiter.allow() is True
    assert limiter.allow() is False
    limiter.clear()
    assert limiter.allow() is True


def test_rate_limit_config_resolvers_and_fallbacks(monkeypatch):
    """
    Tests environment variable resolution and invalid format fallbacks.
    """
    from src.security.rate_limit.config import (
        DEFAULT_LOCKOUT_DURATION_SECONDS,
        DEFAULT_MAX_ATTEMPTS,
        DEFAULT_MAX_TRACKED_KEYS,
        DEFAULT_SIGNUP_MAX_EVENTS,
        DEFAULT_SIGNUP_WINDOW_SECONDS,
        get_auth_lockout_seconds,
        get_auth_max_attempts,
        get_auth_max_tracked_keys,
        get_signup_max_events,
        get_signup_window_seconds,
    )

    # Test valid env overrides
    monkeypatch.setenv("AUTH_MAX_ATTEMPTS", "10")
    monkeypatch.setenv("AUTH_LOCKOUT_SECONDS", "60")
    monkeypatch.setenv("AUTH_MAX_TRACKED_KEYS", "5000")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", "50")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_WINDOW_SECONDS", "120")

    assert get_auth_max_attempts() == 10
    assert get_auth_lockout_seconds() == 60
    assert get_auth_max_tracked_keys() == 5000
    assert get_signup_max_events() == 50
    assert get_signup_window_seconds() == 120

    # Test invalid env overrides fall back to defaults
    monkeypatch.setenv("AUTH_MAX_ATTEMPTS", "invalid")
    monkeypatch.setenv("AUTH_LOCKOUT_SECONDS", "invalid")
    monkeypatch.setenv("AUTH_MAX_TRACKED_KEYS", "invalid")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_MAX_EVENTS", "invalid")
    monkeypatch.setenv("SIGNUP_RATE_LIMIT_WINDOW_SECONDS", "invalid")

    assert get_auth_max_attempts() == DEFAULT_MAX_ATTEMPTS
    assert get_auth_lockout_seconds() == DEFAULT_LOCKOUT_DURATION_SECONDS
    assert get_auth_max_tracked_keys() == DEFAULT_MAX_TRACKED_KEYS
    assert get_signup_max_events() == DEFAULT_SIGNUP_MAX_EVENTS
    assert get_signup_window_seconds() == DEFAULT_SIGNUP_WINDOW_SECONDS
