from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, str_enum
from app.models.enums import Category, Period, Priority


class Todo(TimestampMixin, Base):
    __tablename__ = "todos"
    # Most queries are "this user's todos, by due date", so index exactly that.
    __table_args__ = (Index("ix_todos_user_id_due_date", "user_id", "due_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    period: Mapped[Period] = mapped_column(str_enum(Period))
    priority: Mapped[Priority] = mapped_column(str_enum(Priority))
    category: Mapped[Category] = mapped_column(str_enum(Category))
    due_date: Mapped[date | None] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
