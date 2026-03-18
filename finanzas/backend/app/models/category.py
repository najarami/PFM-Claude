import uuid

from sqlalchemy import Boolean, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(10))
    color: Mapped[str | None] = mapped_column(String(7))  # hex color
    is_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=99)

    keywords: Mapped[list["CategoryKeyword"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")  # noqa: F821
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category", cascade="all, delete-orphan")  # noqa: F821


class CategoryKeyword(Base):
    __tablename__ = "category_keywords"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, default="contains")
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    category: Mapped["Category"] = relationship(back_populates="keywords")
