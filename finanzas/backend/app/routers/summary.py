from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.summary import CategoryBreakdownSchema, MonthlySummarySchema
from app.services.summary_service import get_monthly_summary

router = APIRouter(tags=["summary"])


@router.get("/summary/{year}/{month}", response_model=MonthlySummarySchema)
async def monthly_summary(
    year: int,
    month: int,
    currency: str = Query("CLP", description="Currency filter: CLP or USD"),
    session: AsyncSession = Depends(get_session),
):
    summary = await get_monthly_summary(year, month, session, currency=currency)
    return MonthlySummarySchema(
        year=summary.year,
        month=summary.month,
        total_income=summary.total_income,
        total_expense=summary.total_expense,
        net=summary.net,
        transaction_count=summary.transaction_count,
        by_category=[
            CategoryBreakdownSchema(
                category_id=b.category_id,
                category_name=b.category_name,
                category_slug=b.category_slug,
                icon=b.icon,
                color=b.color,
                amount=b.amount,
                count=b.count,
                pct_of_total=b.pct_of_total,
            )
            for b in summary.by_category
        ],
    )
