"""cpu_times: the counters of /proc/stat and the busy share between two samples."""

from core.system_health.cpu_times import (
    CpuSample,
    CpuTimes,
    parse_cpu_sample,
    usage_between,
)

# Idle is the fourth counter plus iowait; total is the sum of the first eight counters.
STAT_TEXT = (
    "cpu  1000 0 500 8000 200 0 100 0 0 0\n"
    "cpu0 500 0 250 4000 100 0 50 0 0 0\n"
    "cpu1 500 0 250 4000 100 0 50 0 0 0\n"
    "intr 999 0 0\n"
    "ctxt 42\n"
)


def test_parses_the_aggregate_and_per_core_lines():
    sample = parse_cpu_sample(STAT_TEXT)

    assert sample.overall == CpuTimes(idle=8200, total=9800)
    assert sample.cores == {
        0: CpuTimes(idle=4100, total=4900),
        1: CpuTimes(idle=4100, total=4900),
    }


def test_skips_lines_that_do_not_hold_counters():
    text = (
        "cpu  1 2\n"  # too few counters
        "cpu2x 1 2 3 4 5 6 7 8\n"  # the label is not a plain core number
        "cpux 1 2 3 4 5\n"  # the label does not end in a number
        "cpu3 1 two 3 4 5\n"  # a counter that is not a number
        "\n"
        "cpu4 10 0 10 80 0\n"  # five counters are enough
    )

    sample = parse_cpu_sample(text)

    assert sample.overall is None
    assert sample.cores == {4: CpuTimes(idle=80, total=100)}


def test_an_empty_stat_file_gives_an_empty_sample():
    assert parse_cpu_sample("") == CpuSample()


def test_busy_share_is_the_non_idle_part_of_the_time_that_passed():
    before = parse_cpu_sample(STAT_TEXT)
    after = parse_cpu_sample(
        "cpu  1400 0 500 8600 200 0 100 0 0 0\n"  # +1000 total, +600 idle: 40% busy
        "cpu0 900 0 250 4100 100 0 50 0 0 0\n"  # +500 total, +100 idle: 80% busy
        "cpu1 500 0 250 4000 100 0 50 0 0 0\n"  # no time passed: unknown
        "cpu5 100 0 0 900 0 0 0 0 0 0\n"  # a core the first sample did not have
    )

    usage = usage_between(before, after)

    assert usage.overall == 40.0
    assert usage.per_core == {0: 80.0, 1: None, 5: None}


def test_no_time_passing_or_a_counter_going_backwards_gives_unknown():
    before = parse_cpu_sample(STAT_TEXT)

    assert usage_between(before, before).overall is None
    rebooted = parse_cpu_sample("cpu  10 0 5 80 2 0 1 0 0 0\n")
    assert usage_between(before, rebooted).overall is None


def test_idle_growing_faster_than_the_total_is_refused():
    before = parse_cpu_sample("cpu  100 0 0 10 0 0 0 0\n")
    after = parse_cpu_sample("cpu  0 0 0 200 0 0 0 0\n")

    assert usage_between(before, after).overall is None


def test_a_missing_sample_gives_unknown_usage():
    after = parse_cpu_sample(STAT_TEXT)

    from_nothing = usage_between(CpuSample(), after)
    to_nothing = usage_between(after, CpuSample())

    assert from_nothing.overall is None
    assert from_nothing.per_core == {0: None, 1: None}
    assert to_nothing.overall is None
