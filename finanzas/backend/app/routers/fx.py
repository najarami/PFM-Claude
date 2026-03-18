from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.fx_service import FxRateUnavailable, get_rate

router = APIRouter(tags=["fx"])


@router.get("/fx/rate")
async def get_fx_rate(
    from_currency: str = Query(..., description="Source currency, e.g. USD"),
    to_currency: str = Query(..., description="Target currency, e.g. CLP"),
    rate_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    session: AsyncSession = Depends(get_session),
):
    """Return the exchange rate for a currency pair on a given date.

    Rate is fetched from cache (DB) or Frankfurter API and cached for future use.
    """
    try:
        rate = await get_rate(from_currency, to_currency, rate_date, session)
    except FxRateUnavailable as exc:
        raise HTTPException(
            status_code=422,
            detail=f"FX rate unavailable for {exc.from_currency}->{exc.to_currency} on {exc.rate_date}",
        )
    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate_date": rate_date.isoformat(),
        "rate": float(rate),
    }
