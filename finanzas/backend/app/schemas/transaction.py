import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class TransactionRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    date: date
    description: str
    amount: float
    currency: str
    transaction_type: str
    category_id: Optional[uuid.UUID]
    category_name: Optional[str] = None
    category_slug: Optional[str] = None
    category_icon: Optional[str] = None
    category_color: Optional[str] = None
    is_auto_categorized: bool
    is_duplicate: bool
    month: int
    year: int
    source_file: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionUpdateCategory(BaseModel):
    category_id: Optional[uuid.UUID]


class TransactionUpdateNotes(BaseModel):
    notes: str


class PaginatedTransactions(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
    total_pages: int
