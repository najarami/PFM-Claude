import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)  # checking | credit_card | digital_wallet
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CLP")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")  # noqa: F821
    upload_logs: Mapped[list["UploadLog"]] = relationship(back_populates="account")  # noqa: F821
