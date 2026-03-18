from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.summary import MonthComparisonSchema
from app.services.summary_service import get_comparison

router = APIRouter(tags=["comparison"])


@router.get("/comparison", response_model=list[MonthComparisonSchema])
async def comparison(
    months: list[str] = Query(..., description="List of 'YYYY-MM' strings, e.g. 2024-01"),
    currency: str = Query("CLP", description="Currency: CLP or USD"),
    session: AsyncSession = Depends(get_session),
):
    """
    Compare up to 12 months side by side.
    Pass multiple ?months=2024-01&months=2024-02 query params.
    """
    years_months = []
    for m in months[:12]:
        parts = m.split("-")
        if len(parts) == 2:
            years_months.append((int(parts[0]), int(parts[1])))

    snapshots = await get_comparison(years_months, session, currency=currency)

    return [
        MonthComparisonSchema(
            year=s["year"],
            month=s["month"],
            total_income=s["total_income"],
            total_expense=s["total_expense"],
            net=s["net"],
            by_category=s["by_category"],
        )
        for s in snapshots
    ]
