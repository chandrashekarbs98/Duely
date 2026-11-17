"""Response shapes for the Home page, reminders, and the internal reminder job."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.finance import FinanceRead
from app.schemas.todo import TodoRead


class MonthSummary(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    net: Decimal
    budget: Decimal | None
    budget_remaining: Decimal | None
    budget_used_percent: int | None


class HomeCounts(BaseModel):
    open_todos: int
    overdue_todos: int
    completed_this_week: int


class HomeResponse(BaseModel):
    today: date
    currency: str
    urgent_todos: list[TodoRead]
    month: MonthSummary
    upcoming_payments: list[FinanceRead]
    counts: HomeCounts


class RemindersResponse(BaseModel):
    today: date
    overdue_todos: list[TodoRead]
    due_today_todos: list[TodoRead]
    upcoming_todos: list[TodoRead]
    overdue_payments: list[FinanceRead]
    due_today_payments: list[FinanceRead]
    upcoming_payments: list[FinanceRead]


class SendResult(BaseModel):
    sent_to: str


class ReminderRunResult(BaseModel):
    users_checked: int
    emails_sent: int
