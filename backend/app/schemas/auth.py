from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field

from app.schemas.common import InputModel, Money, ORMModel


def _max_72_bytes(value: str) -> str:
    # bcrypt only looks at the first 72 bytes; refuse longer passwords instead of truncating.
    if len(value.encode()) > 72:
        raise ValueError("Password must be at most 72 bytes.")
    return value


# Emails are compared case-insensitively, so store and look them up in lower case.
Email = Annotated[EmailStr, AfterValidator(str.lower)]
NewPassword = Annotated[str, Field(min_length=8, max_length=72), AfterValidator(_max_72_bytes)]


class RegisterRequest(InputModel):
    email: Email
    password: NewPassword
    name: str = Field(min_length=1, max_length=100)


class LoginRequest(InputModel):
    email: Email
    password: str = Field(min_length=1, max_length=72)


class UserUpdate(InputModel):
    """PATCH: only the fields sent are changed. Send monthly_budget: null to clear it."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    monthly_budget: Money | None = None
    email_reminders: bool | None = None


class UserRead(ORMModel):
    id: int
    email: str
    name: str
    monthly_budget: Decimal | None
    email_reminders: bool
    created_at: datetime


class MeResponse(UserRead):
    currency: str
