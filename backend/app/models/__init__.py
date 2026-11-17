"""Importing every model here registers it on Base.metadata, which Alembic compares against."""

from app.models.base import Base
from app.models.finance import FinanceEntry
from app.models.todo import Todo
from app.models.user import User

__all__ = ["Base", "FinanceEntry", "Todo", "User"]
