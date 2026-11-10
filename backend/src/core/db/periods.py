"""Report periods shared by the analytics reads: a day, a Monday week, a calendar month."""

from datetime import date, timedelta
from typing import Literal

__all__ = ["Period", "period_bounds", "period_params"]

Period = Literal["day", "week", "month"]


def period_bounds(period: Period, day: date) -> tuple[date, date, date]:
    """(previous start, start, exclusive end) of the period that holds day."""
    if period == "day":
        return day - timedelta(days=1), day, day + timedelta(days=1)
    if period == "week":
        start = day - timedelta(days=day.weekday())
        return start - timedelta(days=7), start, start + timedelta(days=7)
    start = day.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1)
    return (start - timedelta(days=1)).replace(day=1), start, end


def period_params(period: Period, day: date) -> dict[str, str]:
    """The bounds as ISO dates, ready to compare with SQLite's UTC timestamps.

    ponytail: timestamps are UTC and compared by date, so a row written after
    18:00 in Guatemala (UTC-6) on a period's last day counts toward the next one.
    """
    previous, start, end = period_bounds(period, day)
    return {"previous": str(previous), "start": str(start), "end": str(end)}
