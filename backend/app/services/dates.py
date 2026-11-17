"""Date helpers used by business rules. Pure functions: easy to unit test."""

import calendar
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models.enums import Period


def add_months(d: date, months: int) -> date:
    """Move by whole months, clamping the day: Jan 31 + 1 month = Feb 28 (or 29)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def next_occurrence(d: date, period: Period) -> date:
    if period is Period.DAILY:
        return d + timedelta(days=1)
    if period is Period.MONTHLY:
        return add_months(d, 1)
    return add_months(d, 12)  # Feb 29 + 1 year = Feb 28


def month_bounds(d: date) -> tuple[date, date]:
    first = d.replace(day=1)
    last = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return first, last


def months_between(start: date, end: date) -> list[str]:
    """Every month label from start to end inclusive, e.g. ["2026-01", "2026-02"]."""
    labels: list[str] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        labels.append(f"{cursor.year:04d}-{cursor.month:02d}")
        cursor = add_months(cursor, 1)
    return labels


def start_of_week(today: date, tz: str) -> datetime:
    """Monday 00:00 of this week, in the app time zone, as an aware datetime."""
    monday = today - timedelta(days=today.weekday())
    return datetime.combine(monday, time.min, tzinfo=ZoneInfo(tz))
