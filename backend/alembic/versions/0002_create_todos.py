"""create todos

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("category", sa.String(length=10), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_todos_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_todos"),
        # The database itself refuses bad values, even if a bug skips Pydantic validation.
        sa.CheckConstraint("period IN ('daily', 'monthly', 'yearly')", name="ck_todos_period"),
        sa.CheckConstraint("priority IN ('high', 'medium', 'low')", name="ck_todos_priority"),
        sa.CheckConstraint(
            "category IN ('home', 'office', 'self', 'misc')", name="ck_todos_category"
        ),
    )
    op.create_index("ix_todos_user_id_due_date", "todos", ["user_id", "due_date"])


def downgrade() -> None:
    op.drop_index("ix_todos_user_id_due_date", table_name="todos")
    op.drop_table("todos")
