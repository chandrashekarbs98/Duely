import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_reminder_service
from app.core.errors import AuthError, NotFoundError
from app.schemas.dashboard import ReminderRunResult, RemindersResponse, SendResult
from app.services.reminders import ReminderService

router = APIRouter(tags=["reminders"])
Service = Annotated[ReminderService, Depends(get_reminder_service)]


@router.get("/reminders", response_model=RemindersResponse)
def reminders(user: CurrentUser, service: Service) -> RemindersResponse:
    return service.reminders(user)


@router.post("/reminders/test-email", response_model=SendResult)
def send_test_email(user: CurrentUser, service: Service) -> SendResult:
    return SendResult(sent_to=service.send_test_digest(user))


@router.post("/internal/reminders/run", response_model=ReminderRunResult, include_in_schema=False)
def run_daily_reminders(
    service: Service, x_cron_secret: Annotated[str | None, Header()] = None
) -> ReminderRunResult:
    """Called by a scheduler (GitHub Actions), not by people. Protected by a shared secret."""
    expected = get_settings().cron_secret
    if not expected:
        raise NotFoundError("Not found.")  # feature switched off: pretend the route is absent
    # compare_digest takes the same time whether the first or last character differs.
    if not x_cron_secret or not secrets.compare_digest(x_cron_secret, expected):
        raise AuthError("Invalid cron secret.")
    return service.run_daily()
