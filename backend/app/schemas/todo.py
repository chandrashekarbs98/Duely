from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import Category, Period, Priority
from app.schemas.common import InputModel, ORMModel


class TodoWrite(InputModel):
    """Body for POST (create) and PUT (full replace)."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    period: Period = Period.DAILY
    priority: Priority = Priority.MEDIUM
    category: Category = Category.MISC
    due_date: date | None = None


class TodoRead(ORMModel):
    id: int
    title: str
    description: str | None
    period: Period
    priority: Priority
    category: Category
    due_date: date | None
    completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TodoQuery(BaseModel):
    """Query string for GET /api/todos. FastAPI fills this model from ?key=value pairs."""

    model_config = {"extra": "forbid"}

    period: Period | None = None
    priority: Priority | None = None
    category: Category | None = None
    completed: bool | None = None
    due_from: date | None = None
    due_to: date | None = None
    q: str | None = Field(default=None, max_length=100)
    sort: Literal["due_date", "priority", "created_at", "title"] = "due_date"
    order: Literal["asc", "desc"] = "asc"
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
