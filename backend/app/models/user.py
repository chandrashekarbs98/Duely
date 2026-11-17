from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Added in migration 0004 (settings).
    monthly_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    email_reminders: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    last_reminder_sent_on: Mapped[date | None] = mapped_column(Date)
