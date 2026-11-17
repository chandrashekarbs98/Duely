"""user settings: monthly budget and email reminders

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-17

Adding columns to an existing table: new columns are nullable or have a server default,
so rows that already exist stay valid without a data backfill.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("monthly_budget", sa.Numeric(12, 2), nullable=True))
    op.add_column(
        "users",
        sa.Column("email_reminders", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("users", sa.Column("last_reminder_sent_on", sa.Date(), nullable=True))
    op.create_check_constraint(
        "ck_users_monthly_budget_positive",
        "users",
        "monthly_budget IS NULL OR monthly_budget > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_monthly_budget_positive", "users", type_="check")
    op.drop_column("users", "last_reminder_sent_on")
    op.drop_column("users", "email_reminders")
    op.drop_column("users", "monthly_budget")
