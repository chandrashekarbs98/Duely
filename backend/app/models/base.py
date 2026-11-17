from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Predictable constraint names, so migrations can refer to them (e.g. to drop one later).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Parent class for all SQLAlchemy models. Alembic reads Base.metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def str_enum(enum_cls: type[StrEnum]) -> Enum:
    """Store a Python enum as VARCHAR(10) holding its value ("high", not "HIGH").

    The allowed values are enforced by a CHECK constraint written in the migration.
    VARCHAR + CHECK is easier to change later than a native Postgres ENUM type.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=10,
        values_callable=lambda members: [m.value for m in members],
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
