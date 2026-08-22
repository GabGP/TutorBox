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
