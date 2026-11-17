"""FastAPI dependencies: how each request gets its DB session, current user and services.

Depends() builds these per request. Tests swap any of them with app.dependency_overrides.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.email import EmailSender, get_email_sender
from app.core.errors import AuthError
from app.core.security import decode_access_token
from app.models import User
from app.repositories.finance import FinanceRepository
from app.repositories.health import HealthRepository
from app.repositories.todo import TodoRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.finance import FinanceService
from app.services.home import HomeService
from app.services.reminders import ReminderService
from app.services.todo import TodoService

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    """Authentication: who is calling? Reads the JWT from the httpOnly cookie."""
    token = request.cookies.get(get_settings().auth_cookie_name)
    user_id = decode_access_token(token) if token else None
    user = UserRepository(db).get(user_id) if user_id is not None else None
    if user is None:
        raise AuthError("Not authenticated.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(UserRepository(db))


def get_todo_service(db: DbSession) -> TodoService:
    return TodoService(TodoRepository(db))


def get_finance_service(db: DbSession) -> FinanceService:
    return FinanceService(FinanceRepository(db))


def get_home_service(db: DbSession) -> HomeService:
    return HomeService(TodoRepository(db), FinanceRepository(db))


def get_reminder_service(
    db: DbSession, sender: Annotated[EmailSender, Depends(get_email_sender)]
) -> ReminderService:
    return ReminderService(UserRepository(db), TodoRepository(db), FinanceRepository(db), sender)


def get_health_repository(db: DbSession) -> HealthRepository:
    return HealthRepository(db)
