from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.orm import Session

from app.models import FinanceEntry
from app.models.enums import Category, EntryKind, EntryStatus, Priority
from app.schemas.finance import FinanceFilters

PRIORITY_RANK = case(
    (FinanceEntry.priority == Priority.HIGH, 0),
    (FinanceEntry.priority == Priority.MEDIUM, 1),
    else_=2,
)

ZERO = Decimal("0.00")

# SUM(CASE WHEN kind = 'income' THEN amount ELSE 0 END): one pass, two totals.
INCOME_SUM = func.coalesce(
    func.sum(case((FinanceEntry.kind == EntryKind.INCOME, FinanceEntry.amount), else_=0)), 0
)
EXPENSE_SUM = func.coalesce(
    func.sum(case((FinanceEntry.kind == EntryKind.EXPENSE, FinanceEntry.amount), else_=0)), 0
)


@dataclass(frozen=True)
class Totals:
    income: Decimal
    expense: Decimal


class FinanceRepository:
    """Every method takes user_id and filters by it. This is the data isolation rule."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- reads -------------------------------------------------------------------------

    def get(self, user_id: int, entry_id: int) -> FinanceEntry | None:
        stmt = select(FinanceEntry).where(
            FinanceEntry.id == entry_id, FinanceEntry.user_id == user_id
        )
        return self.db.scalar(stmt)

    def _conditions(self, user_id: int, f: FinanceFilters) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [FinanceEntry.user_id == user_id]
        if f.period:
            conditions.append(FinanceEntry.period == f.period)
        if f.priority:
            conditions.append(FinanceEntry.priority == f.priority)
        if f.category:
            conditions.append(FinanceEntry.category == f.category)
        if f.kind:
            conditions.append(FinanceEntry.kind == f.kind)
        if f.status:
            conditions.append(FinanceEntry.status == f.status)
        if f.date_from:
            conditions.append(FinanceEntry.entry_date >= f.date_from)
        if f.date_to:
            conditions.append(FinanceEntry.entry_date <= f.date_to)
        if f.q:
            conditions.append(FinanceEntry.title.ilike(f"%{f.q}%"))
        return conditions

    def _ordering(self, f: FinanceFilters) -> Any:
        column: Any = {
            "entry_date": FinanceEntry.entry_date,
            "amount": FinanceEntry.amount,
            "priority": PRIORITY_RANK,
            "created_at": FinanceEntry.created_at,
        }[f.sort]
        return column.desc() if f.order == "desc" else column.asc()

    def search(
        self, user_id: int, f: FinanceFilters, limit: int, offset: int
    ) -> tuple[list[FinanceEntry], int]:
        conditions = self._conditions(user_id, f)
        total = (
            self.db.scalar(select(func.count()).select_from(FinanceEntry).where(*conditions)) or 0
        )
        stmt = (
            select(FinanceEntry)
            .where(*conditions)
            .order_by(self._ordering(f), FinanceEntry.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt)), total

    def search_all(self, user_id: int, f: FinanceFilters, cap: int) -> list[FinanceEntry]:
        stmt = (
            select(FinanceEntry)
            .where(*self._conditions(user_id, f))
            .order_by(self._ordering(f), FinanceEntry.id.desc())
            .limit(cap)
        )
        return list(self.db.scalars(stmt))

    def planned_expenses_between(
        self, user_id: int, start: date | None, end: date
    ) -> list[FinanceEntry]:
        """Planned (unpaid) expenses dated in [start, end]. start=None means "up to end"."""
        conditions = [
            FinanceEntry.user_id == user_id,
            FinanceEntry.kind == EntryKind.EXPENSE,
            FinanceEntry.status == EntryStatus.PLANNED,
            FinanceEntry.entry_date <= end,
        ]
        if start is not None:
            conditions.append(FinanceEntry.entry_date >= start)
        stmt = (
            select(FinanceEntry)
            .where(*conditions)
            .order_by(FinanceEntry.entry_date, FinanceEntry.id)
        )
        return list(self.db.scalars(stmt))

    # ---- aggregates (paid entries only) ------------------------------------------------

    def _paid_in_range(self, user_id: int, start: date, end: date) -> list[ColumnElement[bool]]:
        return [
            FinanceEntry.user_id == user_id,
            FinanceEntry.status == EntryStatus.PAID,
            FinanceEntry.entry_date >= start,
            FinanceEntry.entry_date <= end,
        ]

    def totals(self, user_id: int, start: date, end: date) -> Totals:
        row = self.db.execute(
            select(INCOME_SUM, EXPENSE_SUM).where(*self._paid_in_range(user_id, start, end))
        ).one()
        return Totals(income=Decimal(row[0]), expense=Decimal(row[1]))

    def totals_by_category(self, user_id: int, start: date, end: date) -> dict[Category, Totals]:
        stmt = (
            select(FinanceEntry.category, INCOME_SUM, EXPENSE_SUM)
            .where(*self._paid_in_range(user_id, start, end))
            .group_by(FinanceEntry.category)
        )
        return {
            Category(cat): Totals(Decimal(inc), Decimal(exp))
            for cat, inc, exp in self.db.execute(stmt)
        }

    def totals_by_month(self, user_id: int, start: date, end: date) -> dict[str, Totals]:
        month = func.to_char(FinanceEntry.entry_date, "YYYY-MM")
        stmt = (
            select(month, INCOME_SUM, EXPENSE_SUM)
            .where(*self._paid_in_range(user_id, start, end))
            .group_by(month)
        )
        return {m: Totals(Decimal(inc), Decimal(exp)) for m, inc, exp in self.db.execute(stmt)}

    # ---- writes ------------------------------------------------------------------------

    def create(self, user_id: int, fields: dict[str, Any]) -> FinanceEntry:
        entry = FinanceEntry(user_id=user_id, **fields)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: FinanceEntry, fields: dict[str, Any]) -> FinanceEntry:
        for name, value in fields.items():
            setattr(entry, name, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: FinanceEntry) -> None:
        self.db.delete(entry)
        self.db.commit()
