import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, SmallInteger, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    upload_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("upload_logs.id"))

    # Core fields
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_description: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)  # negative = expense, positive = income
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CLP")

    # Classification
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # income | expense | transfer
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    is_auto_categorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Deduplication
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    dedup_hash: Mapped[str | None] = mapped_column(String(64))

    # Derived (materialized for query performance)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # Metadata
    source_file: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account: Mapped["Account"] = relationship(back_populates="transactions")  # noqa: F821
    category: Mapped["Category | None"] = relationship(back_populates="transactions")  # noqa: F821
