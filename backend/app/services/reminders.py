"""Reminders: what is overdue, due today, and coming up, plus the daily email digest."""

import html
import logging
from collections.abc import Callable
from datetime import date, timedelta

from app.core import clock
from app.core.config import get_settings
from app.core.email import Email, EmailSender
from app.core.errors import ServiceUnavailableError, TooManyRequestsError
from app.core.rate_limit import test_email_cooldown, test_emails_global, test_emails_per_user
from app.models import FinanceEntry, Todo, User
from app.repositories.finance import FinanceRepository
from app.repositories.todo import TodoRepository
from app.repositories.user import UserRepository
from app.schemas.dashboard import ReminderRunResult, RemindersResponse
from app.schemas.finance import FinanceRead
from app.schemas.todo import TodoRead

logger = logging.getLogger(__name__)
UPCOMING_DAYS = 7


def _split_by_day[T](
    items: list[T], today: date, get_date: Callable[[T], date | None]
) -> tuple[list[T], list[T], list[T]]:
    """Split items into (before today, today, after today)."""
    overdue: list[T] = []
    due_today: list[T] = []
    upcoming: list[T] = []
    for item in items:
        day = get_date(item)
        if day is None:
            continue
        (overdue if day < today else due_today if day == today else upcoming).append(item)
    return overdue, due_today, upcoming


class ReminderService:
    def __init__(
        self,
        users: UserRepository,
        todos: TodoRepository,
        entries: FinanceRepository,
        sender: EmailSender,
    ) -> None:
        self.users = users
        self.todos = todos
        self.entries = entries
        self.sender = sender

    # ---- what is due -------------------------------------------------------------------

    def reminders(self, user: User) -> RemindersResponse:
        today = clock.today()
        horizon = today + timedelta(days=UPCOMING_DAYS)

        # One query each, then split in Python: fewer round trips to the database.
        todos = self.todos.open_due_between(user.id, None, horizon)
        payments = self.entries.planned_expenses_between(user.id, None, horizon)
        t_over, t_today, t_next = _split_by_day(todos, today, lambda t: t.due_date)
        p_over, p_today, p_next = _split_by_day(payments, today, lambda p: p.entry_date)

        def as_todos(items: list[Todo]) -> list[TodoRead]:
            return [TodoRead.model_validate(i) for i in items]

        def as_payments(items: list[FinanceEntry]) -> list[FinanceRead]:
            return [FinanceRead.model_validate(i) for i in items]

        return RemindersResponse(
            today=today,
            overdue_todos=as_todos(t_over),
            due_today_todos=as_todos(t_today),
            upcoming_todos=as_todos(t_next),
            overdue_payments=as_payments(p_over),
            due_today_payments=as_payments(p_today),
            upcoming_payments=as_payments(p_next),
        )

    # ---- email -------------------------------------------------------------------------

    def _digest_email(self, user: User, r: RemindersResponse) -> Email:
        currency = get_settings().currency
        sections: list[tuple[str, list[str]]] = [
            ("Overdue to-dos", [f"{t.title} (due {t.due_date})" for t in r.overdue_todos]),
            ("To-dos due today", [t.title for t in r.due_today_todos]),
            (
                "Overdue payments",
                [
                    f"{p.title}: {currency} {p.amount} (was due {p.entry_date})"
                    for p in r.overdue_payments
                ],
            ),
            (
                "Payments due today",
                [f"{p.title}: {currency} {p.amount}" for p in r.due_today_payments],
            ),
            (
                "Coming up this week",
                [f"{t.title} on {t.due_date}" for t in r.upcoming_todos]
                + [
                    f"{p.title}: {currency} {p.amount} on {p.entry_date}"
                    for p in r.upcoming_payments
                ],
            ),
        ]
        sections = [(title, lines) for title, lines in sections if lines]
        link = get_settings().app_url.rstrip("/") + "/reminders"

        if not sections:
            text = "You're all caught up. Nothing is due in the next 7 days."
            body_html = f"<p>{html.escape(text)}</p>"
        else:
            text = "\n\n".join(
                f"{title}\n" + "\n".join(f"- {line}" for line in lines) for title, lines in sections
            )
            # html.escape: titles are user input; never put raw user text into HTML.
            body_html = "".join(
                f"<h3 style='margin:16px 0 4px'>{html.escape(title)}</h3><ul>"
                + "".join(f"<li>{html.escape(line)}</li>" for line in lines)
                + "</ul>"
                for title, lines in sections
            )

        greeting = f"Hi {user.name},"
        return Email(
            to_address=user.email,
            to_name=user.name,
            subject=f"Your reminders for {r.today:%d %b %Y}",
            text=f"{greeting}\n\n{text}\n\nOpen Duely: {link}\n",
            html=(
                "<div style='font-family:system-ui,sans-serif;max-width:560px'>"
                f"<p>{html.escape(greeting)}</p>{body_html}"
                f"<p><a href='{html.escape(link)}'>Open Duely</a></p></div>"
            ),
        )

    def send_test_digest(self, user: User) -> str:
        # Each test email is real and paid for from the Brevo quota, and sign-up does not
        # prove you own the address. Without limits, anyone could register a stranger's
        # email and press the button in a loop: spam sent in our name, quota gone.
        key = str(user.id)
        if not test_email_cooldown.try_acquire(key):
            raise TooManyRequestsError("You can send one test email every 10 minutes.")
        if not test_emails_per_user.try_acquire(key):
            raise TooManyRequestsError("You've sent 5 test emails today. Try again tomorrow.")
        if not test_emails_global.try_acquire("all"):
            raise TooManyRequestsError("Test emails are paused for today. Try again tomorrow.")
        self.sender.send(self._digest_email(user, self.reminders(user)))
        return user.email

    def run_daily(self) -> ReminderRunResult:
        """Called once a day by the scheduler. Safe to call twice: each user gets one per day."""
        today = clock.today()
        checked = sent = 0
        for user in self.users.reminder_recipients(today):
            checked += 1
            r = self.reminders(user)
            has_items = any(
                [
                    r.overdue_todos,
                    r.due_today_todos,
                    r.overdue_payments,
                    r.due_today_payments,
                    r.upcoming_todos,
                    r.upcoming_payments,
                ]
            )
            if has_items:
                try:
                    self.sender.send(self._digest_email(user, r))
                except ServiceUnavailableError:
                    logger.warning("Reminder email to user %s failed; will retry next run", user.id)
                    continue  # not marked as sent, so a re-run tries again
                sent += 1
            self.users.update(user, {"last_reminder_sent_on": today})
        return ReminderRunResult(users_checked=checked, emails_sent=sent)
