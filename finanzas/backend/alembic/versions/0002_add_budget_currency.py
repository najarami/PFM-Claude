"""Add currency field to budgets table

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add currency column with default CLP
    op.add_column("budgets", sa.Column("currency", sa.String(3), nullable=False, server_default="CLP"))

    # Drop the old unique constraint
    op.drop_constraint("uq_budget_category_month_year", "budgets", type_="unique")

    # Add new unique constraint that includes currency
    op.create_unique_constraint(
        "uq_budget_cat_month_year_currency",
        "budgets",
        ["category_id", "month", "year", "currency"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_budget_cat_month_year_currency", "budgets", type_="unique")
    op.create_unique_constraint(
        "uq_budget_category_month_year",
        "budgets",
        ["category_id", "month", "year"],
    )
    op.drop_column("budgets", "currency")
