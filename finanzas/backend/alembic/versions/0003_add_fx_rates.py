"""Add fx_rates table and fix dedup hash to include currency

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create fx_rates cache table
    op.create_table(
        "fx_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("rate_date", sa.Date, nullable=False),
        sa.Column("from_currency", sa.String(3), nullable=False),
        sa.Column("to_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="frankfurter"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_fx_rate_date_pair",
        "fx_rates",
        ["rate_date", "from_currency", "to_currency"],
    )
    op.create_index(
        "idx_fx_rates_lookup",
        "fx_rates",
        ["rate_date", "from_currency", "to_currency"],
    )

    # Recompute dedup_hash to include currency (fixes cross-currency collision bug)
    # New hash payload: account_id|date|amount|DESCRIPTION|currency
    op.execute("""
        UPDATE transactions
        SET dedup_hash = encode(
            sha256(
                (account_id::text || '|' ||
                 date::text || '|' ||
                 amount::text || '|' ||
                 upper(trim(description)) || '|' ||
                 currency)::bytea
            ),
            'hex'
        )
    """)


def downgrade() -> None:
    op.drop_index("idx_fx_rates_lookup", table_name="fx_rates")
    op.drop_constraint("uq_fx_rate_date_pair", "fx_rates", type_="unique")
    op.drop_table("fx_rates")

    # Revert hash to original format (without currency)
    op.execute("""
        UPDATE transactions
        SET dedup_hash = encode(
            sha256(
                (account_id::text || '|' ||
                 date::text || '|' ||
                 amount::text || '|' ||
                 upper(trim(description)))::bytea
            ),
            'hex'
        )
    """)
