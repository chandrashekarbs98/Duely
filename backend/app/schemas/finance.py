from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import Category, EntryKind, EntryStatus, Period, Priority
from app.schemas.common import InputModel, Money, ORMModel


class FinanceWrite(InputModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    period: Period = Period.DAILY
    priority: Priority = Priority.MEDIUM
    category: Category = Category.MISC
    kind: EntryKind = EntryKind.EXPENSE
    amount: Money
    entry_date: date
    status: EntryStatus = EntryStatus.PAID


class FinanceRead(ORMModel):
    id: int
    title: str
    description: str | None
    period: Period
    priority: Priority
    category: Category
    kind: EntryKind
    amount: Decimal  # serialised as a JSON string, e.g. "199.99"
    entry_date: date
    status: EntryStatus
    created_at: datetime
    updated_at: datetime


class FinanceFilters(BaseModel):
    """Filters shared by the list and the CSV export."""

    model_config = {"extra": "forbid"}

    period: Period | None = None
    priority: Priority | None = None
    category: Category | None = None
    kind: EntryKind | None = None
    status: EntryStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
    q: str | None = Field(default=None, max_length=100)
    sort: Literal["entry_date", "amount", "priority", "created_at"] = "entry_date"
    order: Literal["asc", "desc"] = "desc"


class FinanceQuery(FinanceFilters):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class StatsQuery(BaseModel):
    model_config = {"extra": "forbid"}

    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def _ordered(self) -> "StatsQuery":
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValueError("date_from must be on or before date_to")
            if (self.date_to - self.date_from).days > 366 * 10:
                raise ValueError("The range can be at most 10 years.")
        return self


class CategoryTotal(BaseModel):
    category: Category
    income: Decimal
    expense: Decimal


class MonthTotal(BaseModel):
    month: str  # "2026-11"
    income: Decimal
    expense: Decimal
    net: Decimal


class FinanceStats(BaseModel):
    date_from: date
    date_to: date
    currency: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    by_category: list[CategoryTotal]
    by_month: list[MonthTotal]
