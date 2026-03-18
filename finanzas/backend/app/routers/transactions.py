import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionRead,
    TransactionUpdateCategory,
    TransactionUpdateNotes,
)

router = APIRouter(tags=["transactions"])


def _enrich(tx: Transaction) -> dict:
    """Attach category fields to transaction dict."""
    data = {
        "id": tx.id,
        "account_id": tx.account_id,
        "date": tx.date,
        "description": tx.description,
        "amount": tx.amount,
        "currency": tx.currency,
        "transaction_type": tx.transaction_type,
        "category_id": tx.category_id,
        "category_name": tx.category.name if tx.category else None,
        "category_slug": tx.category.slug if tx.category else None,
        "category_icon": tx.category.icon if tx.category else None,
        "category_color": tx.category.color if tx.category else None,
        "is_auto_categorized": tx.is_auto_categorized,
        "is_duplicate": tx.is_duplicate,
        "month": tx.month,
        "year": tx.year,
        "source_file": tx.source_file,
        "notes": tx.notes,
        "created_at": tx.created_at,
    }
    return data


@router.get("/transactions", response_model=PaginatedTransactions)
async def list_transactions(
    year: Optional[int] = None,
    month: Optional[int] = None,
    account_id: Optional[uuid.UUID] = None,
    category_id: Optional[uuid.UUID] = None,
    transaction_type: Optional[str] = None,
    include_duplicates: bool = False,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    filters = []
    if year is not None:
        filters.append(Transaction.year == year)
    if month is not None:
        filters.append(Transaction.month == month)
    if account_id:
        filters.append(Transaction.account_id == account_id)
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if transaction_type:
        filters.append(Transaction.transaction_type == transaction_type)
    if not include_duplicates:
        filters.append(Transaction.is_duplicate.is_(False))
    if search:
        filters.append(Transaction.description.ilike(f"%{search.upper()}%"))

    count_q = await session.execute(
        select(func.count(Transaction.id)).where(*filters)
    )
    total = int(count_q.scalar() or 0)

    offset = (page - 1) * page_size
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(*filters)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transactions = result.scalars().all()

    return PaginatedTransactions(
        items=[TransactionRead.model_validate(_enrich(tx)) for tx in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.patch("/transactions/{transaction_id}/category", response_model=TransactionRead)
async def update_category(
    transaction_id: uuid.UUID,
    body: TransactionUpdateCategory,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    tx = result.scalar_one()
    tx.category_id = body.category_id
    tx.is_auto_categorized = False
    await session.commit()
    await session.refresh(tx)
    # reload category relationship
    result2 = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    tx = result2.scalar_one()
    return TransactionRead.model_validate(_enrich(tx))


@router.patch("/transactions/{transaction_id}/notes", response_model=TransactionRead)
async def update_notes(
    transaction_id: uuid.UUID,
    body: TransactionUpdateNotes,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    tx = result.scalar_one()
    tx.notes = body.notes
    await session.commit()
    result2 = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    tx = result2.scalar_one()
    return TransactionRead.model_validate(_enrich(tx))
