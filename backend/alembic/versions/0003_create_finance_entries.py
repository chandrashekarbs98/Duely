"""create finance_entries

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finance_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("category", sa.String(length=10), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_finance_entries_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_finance_entries"),
        sa.CheckConstraint("amount > 0", name="ck_finance_entries_amount_positive"),
        sa.CheckConstraint(
            "period IN ('daily', 'monthly', 'yearly')", name="ck_finance_entries_period"
        ),
        sa.CheckConstraint(
            "priority IN ('high', 'medium', 'low')", name="ck_finance_entries_priority"
        ),
        sa.CheckConstraint(
            "category IN ('home', 'office', 'self', 'misc')", name="ck_finance_entries_category"
        ),
        sa.CheckConstraint("kind IN ('expense', 'income')", name="ck_finance_entries_kind"),
        sa.CheckConstraint("status IN ('planned', 'paid')", name="ck_finance_entries_status"),
    )
    op.create_index(
        "ix_finance_entries_user_id_entry_date", "finance_entries", ["user_id", "entry_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_finance_entries_user_id_entry_date", table_name="finance_entries")
    op.drop_table("finance_entries")
