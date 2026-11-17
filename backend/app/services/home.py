from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.core import clock
from app.core.config import get_settings
from app.models import User
from app.repositories.finance import FinanceRepository
from app.repositories.todo import TodoRepository
from app.schemas.dashboard import HomeCounts, HomeResponse, MonthSummary
from app.schemas.finance import FinanceRead
from app.schemas.todo import TodoRead
from app.services.dates import month_bounds, start_of_week
from app.services.finance import q2

URGENT_LIMIT = 10
UPCOMING_DAYS = 7


class HomeService:
    def __init__(self, todos: TodoRepository, entries: FinanceRepository) -> None:
        self.todos = todos
        self.entries = entries

    def month_summary(self, user: User) -> MonthSummary:
        today = clock.today()
        first, last = month_bounds(today)
        totals = self.entries.totals(user.id, first, last)

        budget = user.monthly_budget
        remaining = used_percent = None
        if budget is not None:
            remaining = q2(budget - totals.expense)
            ratio = totals.expense * 100 / budget
            used_percent = int(ratio.quantize(Decimal(1), rounding=ROUND_HALF_UP))

        return MonthSummary(
            month=f"{today.year:04d}-{today.month:02d}",
            income=q2(totals.income),
            expense=q2(totals.expense),
            net=q2(totals.income - totals.expense),
            budget=q2(budget) if budget is not None else None,
            budget_remaining=remaining,
            budget_used_percent=used_percent,
        )

    def home(self, user: User) -> HomeResponse:
        settings = get_settings()
        today = clock.today()
        upcoming = self.entries.planned_expenses_between(
            user.id, today, today + timedelta(days=UPCOMING_DAYS)
        )
        counts = HomeCounts(
            open_todos=self.todos.count_open(user.id),
            overdue_todos=self.todos.count_open(user.id, overdue_before=today),
            completed_this_week=self.todos.count_completed_since(
                user.id, start_of_week(today, settings.app_timezone)
            ),
        )
        return HomeResponse(
            today=today,
            currency=settings.currency,
            urgent_todos=[
                TodoRead.model_validate(t) for t in self.todos.urgent(user.id, today, URGENT_LIMIT)
            ],
            month=self.month_summary(user),
            upcoming_payments=[FinanceRead.model_validate(e) for e in upcoming],
            counts=counts,
        )
