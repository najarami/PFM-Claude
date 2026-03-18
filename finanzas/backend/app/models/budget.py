import uuid

from sqlalchemy import Numeric, SmallInteger, String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("category_id", "month", "year", "currency", name="uq_budget_cat_month_year_currency"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)   # 0 = all months
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)    # 0 = all years
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CLP")
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="budgets")  # noqa: F821
