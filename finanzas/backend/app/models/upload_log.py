import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # csv | pdf
    bank: Mapped[str] = mapped_column(String(50), nullable=False)
    parser_used: Mapped[str] = mapped_column(String(100), nullable=False)
    rows_parsed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_duplicate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped["Account | None"] = relationship(back_populates="upload_logs")  # noqa: F821
