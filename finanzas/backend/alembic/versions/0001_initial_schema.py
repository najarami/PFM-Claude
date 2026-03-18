"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # accounts
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("bank", sa.String(50), nullable=False),
        sa.Column("account_type", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="CLP"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # categories
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("icon", sa.String(10)),
        sa.Column("color", sa.String(7)),
        sa.Column("is_income", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sort_order", sa.SmallInteger, nullable=False, server_default="99"),
    )

    # category_keywords
    op.create_table(
        "category_keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(100), nullable=False),
        sa.Column("match_type", sa.String(20), nullable=False, server_default="contains"),
        sa.Column("priority", sa.SmallInteger, nullable=False, server_default="0"),
    )
    op.create_index("idx_keywords_category", "category_keywords", ["category_id"])

    # upload_logs
    op.create_table(
        "upload_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id")),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("bank", sa.String(50), nullable=False),
        sa.Column("parser_used", sa.String(100), nullable=False),
        sa.Column("rows_parsed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_inserted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_duplicate", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("upload_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_logs.id")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("raw_description", sa.String(500)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="CLP"),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")),
        sa.Column("is_auto_categorized", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_duplicate", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("duplicate_of", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id")),
        sa.Column("dedup_hash", sa.String(64)),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("source_file", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tx_account", "transactions", ["account_id"])
    op.create_index("idx_tx_year_month", "transactions", ["year", "month"])
    op.create_index("idx_tx_category", "transactions", ["category_id"])
    op.create_index("idx_tx_date", "transactions", ["date"])
    op.create_index("idx_tx_dedup_hash", "transactions", ["dedup_hash"])

    # budgets
    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("year", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.UniqueConstraint("category_id", "month", "year", name="uq_budget_category_month_year"),
    )

    # Seed categories
    op.execute("""
        INSERT INTO categories (name, slug, icon, color, is_income, sort_order) VALUES
        ('Alimentación',       'food_dining',    '🍽️', '#F59E0B', false, 1),
        ('Transporte',         'transport',      '🚗', '#3B82F6', false, 2),
        ('Vivienda',           'housing',        '🏠', '#8B5CF6', false, 3),
        ('Entretenimiento',    'entertainment',  '🎬', '#EC4899', false, 4),
        ('Salud',              'health',         '💊', '#10B981', false, 5),
        ('Educación',          'education',      '📚', '#6366F1', false, 6),
        ('Ropa',               'clothing',       '👕', '#F97316', false, 7),
        ('Servicios',          'utilities',      '💡', '#EAB308', false, 8),
        ('Finanzas',           'finance',        '🏦', '#64748B', false, 9),
        ('Otros Gastos',       'other_expense',  '📦', '#6B7280', false, 10),
        ('Sueldo',             'salary',         '💰', '#22C55E', true,  1),
        ('Transferencia Entrada', 'transfer_in', '↩️', '#14B8A6', true,  2),
        ('Otros Ingresos',     'other_income',   '➕', '#84CC16', true,  3)
    """)


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("upload_logs")
    op.drop_table("category_keywords")
    op.drop_table("categories")
    op.drop_table("accounts")
