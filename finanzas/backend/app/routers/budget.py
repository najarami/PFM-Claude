from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.budget import BudgetStatusSchema, BudgetWrite
from app.services.budget_service import get_budget_status, upsert_budget

router = APIRouter(tags=["budget"])


@router.get("/budget", response_model=list[BudgetStatusSchema])
async def get_budgets(
    year: int = Query(...),
    month: int = Query(...),
    currency: str = Query("CLP", description="Currency: CLP or USD"),
    session: AsyncSession = Depends(get_session),
):
    statuses = await get_budget_status(year, month, session, currency=currency)
    return [
        BudgetStatusSchema(
            category_id=s.category_id,
            category_name=s.category_name,
            category_slug=s.category_slug,
            icon=s.icon,
            color=s.color,
            budget_amount=s.budget_amount,
            actual_amount=s.actual_amount,
            remaining=s.remaining,
            pct_used=s.pct_used,
        )
        for s in statuses
    ]


@router.put("/budget/{category_slug}", response_model=dict)
async def set_budget(
    category_slug: str,
    body: BudgetWrite,
    session: AsyncSession = Depends(get_session),
):
    budget = await upsert_budget(
        category_slug=category_slug,
        amount=body.amount,
        month=body.month,
        year=body.year,
        currency=body.currency,
        session=session,
    )
    return {
        "id": str(budget.id),
        "category_slug": category_slug,
        "amount": float(budget.amount),
        "month": budget.month,
        "year": budget.year,
        "currency": budget.currency,
    }
