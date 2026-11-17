import csv
import io
from datetime import date
from decimal import Decimal

from app.core import clock
from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.models import FinanceEntry, User
from app.models.enums import Category, EntryStatus
from app.repositories.finance import FinanceRepository, Totals
from app.schemas.common import Page
from app.schemas.finance import (
    CategoryTotal,
    FinanceFilters,
    FinanceQuery,
    FinanceRead,
    FinanceStats,
    FinanceWrite,
    MonthTotal,
    StatsQuery,
)
from app.services.dates import months_between, next_occurrence

CENT = Decimal("0.01")
EXPORT_CAP = 10_000
ZERO_TOTALS = Totals(Decimal(0), Decimal(0))


def q2(value: Decimal) -> Decimal:
    """Always two decimal places, so JSON shows "0.00" rather than "0"."""
    return value.quantize(CENT)


def _csv_safe(value: str) -> str:
    # Spreadsheet apps execute cells starting with = + - @ as formulas ("CSV injection").
    # A leading apostrophe makes them plain text.
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


class FinanceService:
    def __init__(self, entries: FinanceRepository) -> None:
        self.entries = entries

    def _get_owned(self, user: User, entry_id: int) -> FinanceEntry:
        entry = self.entries.get(user.id, entry_id)
        if entry is None:
            raise NotFoundError("Finance entry not found.")
        return entry

    # ---- CRUD --------------------------------------------------------------------------

    def list(self, user: User, query: FinanceQuery) -> Page[FinanceRead]:
        items, total = self.entries.search(user.id, query, query.limit, query.offset)
        return Page[FinanceRead](
            items=[FinanceRead.model_validate(e) for e in items],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get(self, user: User, entry_id: int) -> FinanceEntry:
        return self._get_owned(user, entry_id)

    def create(self, user: User, data: FinanceWrite) -> FinanceEntry:
        return self.entries.create(user.id, data.model_dump())

    def replace(self, user: User, entry_id: int, data: FinanceWrite) -> FinanceEntry:
        return self.entries.update(self._get_owned(user, entry_id), data.model_dump())

    def mark_paid(self, user: User, entry_id: int) -> FinanceEntry:
        return self.entries.update(self._get_owned(user, entry_id), {"status": EntryStatus.PAID})

    def repeat(self, user: User, entry_id: int) -> FinanceEntry:
        """Copy to the next period (e.g. next month's subscription), as a planned entry."""
        entry = self._get_owned(user, entry_id)
        return self.entries.create(
            user.id,
            {
                "title": entry.title,
                "description": entry.description,
                "period": entry.period,
                "priority": entry.priority,
                "category": entry.category,
                "kind": entry.kind,
                "amount": entry.amount,
                "entry_date": next_occurrence(entry.entry_date, entry.period),
                "status": EntryStatus.PLANNED,
            },
        )

    def delete(self, user: User, entry_id: int) -> None:
        self.entries.delete(self._get_owned(user, entry_id))

    # ---- stats -------------------------------------------------------------------------

    def stats(self, user: User, query: StatsQuery) -> FinanceStats:
        today = clock.today()
        start = query.date_from or date(today.year, 1, 1)
        end = query.date_to or date(today.year, 12, 31)

        totals = self.entries.totals(user.id, start, end)
        by_cat = self.entries.totals_by_category(user.id, start, end)
        by_month = self.entries.totals_by_month(user.id, start, end)

        # Fill gaps with zeros so charts always show every category and month.
        categories = [
            CategoryTotal(
                category=c,
                income=q2(by_cat.get(c, ZERO_TOTALS).income),
                expense=q2(by_cat.get(c, ZERO_TOTALS).expense),
            )
            for c in Category
        ]
        months = []
        for label in months_between(start, end):
            t = by_month.get(label, ZERO_TOTALS)
            months.append(
                MonthTotal(
                    month=label,
                    income=q2(t.income),
                    expense=q2(t.expense),
                    net=q2(t.income - t.expense),
                )
            )

        return FinanceStats(
            date_from=start,
            date_to=end,
            currency=get_settings().currency,
            total_income=q2(totals.income),
            total_expense=q2(totals.expense),
            net=q2(totals.income - totals.expense),
            by_category=categories,
            by_month=months,
        )

    # ---- export ------------------------------------------------------------------------

    def export_csv(self, user: User, filters: FinanceFilters) -> str:
        rows = self.entries.search_all(user.id, filters, EXPORT_CAP)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "date",
                "title",
                "kind",
                "amount",
                "status",
                "category",
                "priority",
                "period",
                "description",
            ]
        )
        for e in rows:
            writer.writerow(
                [
                    e.entry_date.isoformat(),
                    _csv_safe(e.title),
                    e.kind.value,
                    f"{e.amount:.2f}",
                    e.status.value,
                    e.category.value,
                    e.priority.value,
                    e.period.value,
                    _csv_safe(e.description or ""),
                ]
            )
        return buffer.getvalue()
