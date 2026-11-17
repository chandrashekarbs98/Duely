"""The app's single source of "now" and "today".

Servers usually run in UTC, but "due today" must mean today for the user (India by default).
Code calls clock.today() instead of date.today(), and tests monkeypatch it to a fixed date.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def now() -> datetime:
    return datetime.now(UTC)


def today() -> date:
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()
