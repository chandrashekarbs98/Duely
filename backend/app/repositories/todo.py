from datetime import date, datetime
from typing import Any

from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Todo
from app.models.enums import Priority
from app.schemas.todo import TodoQuery

# Sort "high" before "medium" before "low" (alphabetical order would be wrong).
PRIORITY_RANK = case(
    (Todo.priority == Priority.HIGH, 0),
    (Todo.priority == Priority.MEDIUM, 1),
    else_=2,
)


class TodoRepository:
    """Every method takes user_id and filters by it. This is the data isolation rule."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- reads -------------------------------------------------------------------------

    def get(self, user_id: int, todo_id: int) -> Todo | None:
        # Filtering by user_id here means another user's id simply "does not exist" (404).
        stmt = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        return self.db.scalar(stmt)

    def search(self, user_id: int, query: TodoQuery) -> tuple[list[Todo], int]:
        conditions: list[ColumnElement[bool]] = [Todo.user_id == user_id]
        if query.period:
            conditions.append(Todo.period == query.period)
        if query.priority:
            conditions.append(Todo.priority == query.priority)
        if query.category:
            conditions.append(Todo.category == query.category)
        if query.completed is not None:
            conditions.append(Todo.completed.is_(query.completed))
        if query.due_from:
            conditions.append(Todo.due_date >= query.due_from)
        if query.due_to:
            conditions.append(Todo.due_date <= query.due_to)
        if query.q:
            # Bound parameter: the search text is data, never part of the SQL (no injection).
            conditions.append(Todo.title.ilike(f"%{query.q}%"))

        total = self.db.scalar(select(func.count()).select_from(Todo).where(*conditions)) or 0

        sort_column: Any = {
            "due_date": Todo.due_date,
            "priority": PRIORITY_RANK,
            "created_at": Todo.created_at,
            "title": func.lower(Todo.title),
        }[query.sort]
        ordered = sort_column.desc() if query.order == "desc" else sort_column.asc()
        stmt = (
            select(Todo)
            .where(*conditions)
            .order_by(ordered.nulls_last(), Todo.id)  # id breaks ties: stable pages
            .limit(query.limit)
            .offset(query.offset)
        )
        return list(self.db.scalars(stmt)), total

    def urgent(self, user_id: int, today: date, limit: int) -> list[Todo]:
        """Incomplete AND (high priority OR due today or earlier)."""
        stmt = (
            select(Todo)
            .where(
                Todo.user_id == user_id,
                Todo.completed.is_(False),
                or_(Todo.priority == Priority.HIGH, Todo.due_date <= today),
            )
            .order_by(Todo.due_date.asc().nulls_last(), PRIORITY_RANK, Todo.id)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def open_due_between(self, user_id: int, start: date | None, end: date) -> list[Todo]:
        """Incomplete todos due in [start, end]. start=None means "any time up to end"."""
        conditions = [Todo.user_id == user_id, Todo.completed.is_(False), Todo.due_date <= end]
        if start is not None:
            conditions.append(Todo.due_date >= start)
        stmt = select(Todo).where(*conditions).order_by(Todo.due_date, PRIORITY_RANK, Todo.id)
        return list(self.db.scalars(stmt))

    def count_open(self, user_id: int, overdue_before: date | None = None) -> int:
        conditions = [Todo.user_id == user_id, Todo.completed.is_(False)]
        if overdue_before is not None:
            conditions.append(Todo.due_date < overdue_before)
        return self.db.scalar(select(func.count()).select_from(Todo).where(*conditions)) or 0

    def count_completed_since(self, user_id: int, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(Todo)
            .where(Todo.user_id == user_id, Todo.completed_at >= since)
        )
        return self.db.scalar(stmt) or 0

    # ---- writes ------------------------------------------------------------------------

    def create(self, user_id: int, fields: dict[str, Any]) -> Todo:
        todo = Todo(user_id=user_id, **fields)
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def update(self, todo: Todo, fields: dict[str, Any]) -> Todo:
        for name, value in fields.items():
            setattr(todo, name, value)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def delete(self, todo: Todo) -> None:
        self.db.delete(todo)
        self.db.commit()
