from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, str_enum
from app.models.enums import Category, EntryKind, EntryStatus, Period, Priority


class FinanceEntry(TimestampMixin, Base):
    __tablename__ = "finance_entries"
    __table_args__ = (Index("ix_finance_entries_user_id_entry_date", "user_id", "entry_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    period: Mapped[Period] = mapped_column(str_enum(Period))
    priority: Mapped[Priority] = mapped_column(str_enum(Priority))
    category: Mapped[Category] = mapped_column(str_enum(Category))
    kind: Mapped[EntryKind] = mapped_column(str_enum(EntryKind))
    # NUMERIC(12,2): exact decimal, up to 9,999,999,999.99. Floats would turn 0.1 + 0.2
    # into 0.30000000000000004, which is unacceptable for money.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    entry_date: Mapped[date] = mapped_column(Date)
    status: Mapped[EntryStatus] = mapped_column(str_enum(EntryStatus))
