"""Create (or reset) a demo account full of realistic sample data.

    python -m app.scripts.seed_demo                       # demo@example.com, random password
    python -m app.scripts.seed_demo --email you@x.com --password 'long-password'

It reuses the same services as the API, so the data passes the same validation.
"""

import argparse
import secrets
from datetime import timedelta
from decimal import Decimal

from app.core import clock
from app.core.db import SessionLocal
from app.models.enums import Category, EntryKind, EntryStatus, Period, Priority
from app.repositories.finance import FinanceRepository
from app.repositories.todo import TodoRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, UserUpdate
from app.schemas.finance import FinanceWrite
from app.schemas.todo import TodoWrite
from app.services.auth import AuthService
from app.services.dates import add_months
from app.services.finance import FinanceService
from app.services.todo import TodoService


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="demo@example.com")
    parser.add_argument("--password", default=None)
    parser.add_argument("--name", default="Demo User")
    args = parser.parse_args()
    password = args.password or secrets.token_urlsafe(12)

    with SessionLocal() as db:
        users = UserRepository(db)
        existing = users.get_by_email(args.email.lower())
        if existing:
            users.delete(existing)  # cascade removes old demo data
        auth = AuthService(users)
        user, _ = auth.register(
            RegisterRequest(email=args.email, password=password, name=args.name)
        )
        auth.update_profile(user, UserUpdate(monthly_budget=Decimal("40000.00")))

        todos = TodoService(TodoRepository(db))
        finances = FinanceService(FinanceRepository(db))
        today = clock.today()
        day = timedelta(days=1)

        for title, period, priority, category, due in [
            ("Pay electricity bill", Period.MONTHLY, Priority.HIGH, Category.HOME, today),
            ("Submit sprint report", Period.DAILY, Priority.HIGH, Category.OFFICE, today - day),
            ("30 minute walk", Period.DAILY, Priority.MEDIUM, Category.SELF, today),
            (
                "Book dentist appointment",
                Period.YEARLY,
                Priority.LOW,
                Category.SELF,
                today + 5 * day,
            ),
            ("Renew car insurance", Period.YEARLY, Priority.HIGH, Category.MISC, today + 20 * day),
            ("Clean the kitchen", Period.DAILY, Priority.LOW, Category.HOME, today + day),
            (
                "Prepare quarterly review",
                Period.MONTHLY,
                Priority.MEDIUM,
                Category.OFFICE,
                today + 3 * day,
            ),
            ("Read 20 pages", Period.DAILY, Priority.LOW, Category.SELF, None),
        ]:
            todos.create(
                user,
                TodoWrite(
                    title=title, period=period, priority=priority, category=category, due_date=due
                ),
            )
        done = todos.create(
            user,
            TodoWrite(title="Grocery shopping", category=Category.HOME, due_date=today - 2 * day),
        )
        todos.toggle(user, done.id)

        # Three months of history so the charts have something to show.
        for months_back in (2, 1, 0):
            base = add_months(today.replace(day=1), -months_back)
            rows = [
                ("Salary", EntryKind.INCOME, "85000.00", Category.OFFICE, Period.MONTHLY, 1),
                ("Rent", EntryKind.EXPENSE, "22000.00", Category.HOME, Period.MONTHLY, 2),
                ("Groceries", EntryKind.EXPENSE, "6450.75", Category.HOME, Period.DAILY, 6),
                ("Internet", EntryKind.EXPENSE, "999.00", Category.HOME, Period.MONTHLY, 8),
                ("Gym membership", EntryKind.EXPENSE, "1500.00", Category.SELF, Period.MONTHLY, 10),
                ("Team lunch", EntryKind.EXPENSE, "850.50", Category.OFFICE, Period.DAILY, 12),
                (
                    "Streaming subscription",
                    EntryKind.EXPENSE,
                    "199.99",
                    Category.SELF,
                    Period.MONTHLY,
                    15,
                ),
                ("Fuel", EntryKind.EXPENSE, "3200.00", Category.MISC, Period.DAILY, 18),
            ]
            for title, kind, amount, category, period, dom in rows:
                entry_date = base.replace(day=dom)
                if entry_date > today:
                    continue
                finances.create(
                    user,
                    FinanceWrite(
                        title=title,
                        kind=kind,
                        amount=Decimal(amount),
                        category=category,
                        period=period,
                        entry_date=entry_date,
                        status=EntryStatus.PAID,
                    ),
                )

        for title, amount, offset_days, period, priority in [
            ("Credit card bill", "12450.00", 3, Period.MONTHLY, Priority.HIGH),
            ("Phone recharge", "299.00", 0, Period.MONTHLY, Priority.MEDIUM),
            ("Car insurance premium", "18500.00", 20, Period.YEARLY, Priority.HIGH),
            ("Water bill", "450.00", -2, Period.MONTHLY, Priority.MEDIUM),
        ]:
            finances.create(
                user,
                FinanceWrite(
                    title=title,
                    amount=Decimal(amount),
                    period=period,
                    priority=priority,
                    category=Category.HOME,
                    entry_date=today + timedelta(days=offset_days),
                    status=EntryStatus.PLANNED,
                ),
            )

    print(f"Demo account ready.\n  email:    {args.email}\n  password: {password}")


if __name__ == "__main__":
    main()
