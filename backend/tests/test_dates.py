"""Unit tests for pure date helpers (no database, no HTTP)."""

from datetime import date

import pytest

from app.models.enums import Period
from app.services.dates import add_months, month_bounds, months_between, next_occurrence


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # leap year
        (date(2026, 12, 15), 1, date(2027, 1, 15)),
        (date(2026, 3, 31), -1, date(2026, 2, 28)),
        (date(2026, 5, 10), 12, date(2027, 5, 10)),
    ],
)
def test_add_months(start: date, months: int, expected: date) -> None:
    assert add_months(start, months) == expected


def test_next_occurrence() -> None:
    assert next_occurrence(date(2026, 12, 31), Period.DAILY) == date(2027, 1, 1)
    assert next_occurrence(date(2026, 1, 31), Period.MONTHLY) == date(2026, 2, 28)
    assert next_occurrence(date(2028, 2, 29), Period.YEARLY) == date(2029, 2, 28)


def test_month_helpers() -> None:
    assert month_bounds(date(2026, 2, 10)) == (date(2026, 2, 1), date(2026, 2, 28))
    assert months_between(date(2025, 11, 20), date(2026, 2, 1)) == [
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
    ]
