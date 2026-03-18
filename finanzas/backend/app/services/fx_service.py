"""FX rate fetching, caching, and conversion service.

Rates are fetched from api.frankfurter.app (free, no API key required).
All rates are cached in the fx_rates table keyed by (rate_date, from_currency, to_currency).

Rate convention: 1 unit of from_currency = `rate` units of to_currency.
Example: from=USD, to=CLP, rate=978.45 → $1 USD = $978.45 CLP
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.fx_rate import FxRate


class FxRateUnavailable(Exception):
    """Raised when a rate cannot be found in cache or fetched from the API."""
    def __init__(self, from_currency: str, to_currency: str, rate_date: date):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate_date = rate_date
        super().__init__(
            f"FX rate unavailable for {from_currency}->{to_currency} on {rate_date}"
        )


async def get_rate(
    from_currency: str,
    to_currency: str,
    rate_date: date,
    session: AsyncSession,
) -> Decimal:
    """Return units of to_currency per 1 unit of from_currency on rate_date.

    Lookup order:
    1. Same currency → returns 1
    2. DB cache (direct pair)
    3. DB cache (inverse pair) → returns 1/rate
    4. Frankfurter API → stores in DB → returns rate
    """
    if from_currency == to_currency:
        return Decimal("1")

    # Check direct pair in cache
    cached = await _fetch_from_db(from_currency, to_currency, rate_date, session)
    if cached is not None:
        return cached

    # Check inverse pair in cache
    inverse = await _fetch_from_db(to_currency, from_currency, rate_date, session)
    if inverse is not None and inverse != 0:
        return (Decimal("1") / inverse).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    # Fetch from API
    rate = await _fetch_from_api(from_currency, to_currency, rate_date)
    await _store_in_db(from_currency, to_currency, rate_date, rate, session)
    return rate


async def get_rates_bulk(
    pairs: list[tuple[str, str, date]],
    session: AsyncSession,
) -> dict[tuple[str, str, date], Decimal]:
    """Batch fetch rates for multiple (from, to, date) pairs.

    Groups by (from, to) to minimize API calls. Returns a dict
    keyed by (from_currency, to_currency, date).
    """
    result: dict[tuple[str, str, date], Decimal] = {}

    # Deduplicate and filter same-currency pairs
    unique = set()
    for from_c, to_c, d in pairs:
        if from_c != to_c:
            unique.add((from_c, to_c, d))

    # Same-currency pairs resolve immediately
    for from_c, to_c, d in pairs:
        if from_c == to_c:
            result[(from_c, to_c, d)] = Decimal("1")

    if not unique:
        return result

    # Check DB cache for all pairs at once
    missing: set[tuple[str, str, date]] = set()
    for from_c, to_c, d in unique:
        cached = await _fetch_from_db(from_c, to_c, d, session)
        if cached is not None:
            result[(from_c, to_c, d)] = cached
        else:
            # Try inverse
            inverse = await _fetch_from_db(to_c, from_c, d, session)
            if inverse is not None and inverse != 0:
                result[(from_c, to_c, d)] = (Decimal("1") / inverse).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_UP
                )
            else:
                missing.add((from_c, to_c, d))

    # Fetch missing from API, grouped by (from, to) pair to batch by date
    from itertools import groupby
    sorted_missing = sorted(missing, key=lambda x: (x[0], x[1]))
    for (from_c, to_c), group in groupby(sorted_missing, key=lambda x: (x[0], x[1])):
        dates = [d for _, _, d in group]
        for d in dates:
            try:
                rate = await _fetch_from_api(from_c, to_c, d)
                await _store_in_db(from_c, to_c, d, rate, session)
                result[(from_c, to_c, d)] = rate
            except FxRateUnavailable:
                # Leave missing — callers handle KeyError
                pass

    return result


def convert_amount(amount: Decimal, from_currency: str, to_currency: str, rate: Decimal) -> Decimal:
    """Convert amount using the given rate. Returns value with 2 decimal places."""
    if from_currency == to_currency:
        return amount
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def _fetch_from_db(
    from_currency: str,
    to_currency: str,
    rate_date: date,
    session: AsyncSession,
) -> Decimal | None:
    row = await session.execute(
        select(FxRate.rate).where(
            FxRate.from_currency == from_currency,
            FxRate.to_currency == to_currency,
            FxRate.rate_date == rate_date,
        ).limit(1)
    )
    val = row.scalar_one_or_none()
    return Decimal(str(val)) if val is not None else None


async def _fetch_from_api(from_currency: str, to_currency: str, rate_date: date) -> Decimal:
    """Fetch rate from Frankfurter API. Handles weekends/holidays by storing under requested date."""
    url = f"{settings.fx_api_base_url}/{rate_date.isoformat()}"
    params = {"from": from_currency, "to": to_currency}

    async with httpx.AsyncClient(timeout=settings.fx_api_timeout_seconds) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, Exception) as exc:
            raise FxRateUnavailable(from_currency, to_currency, rate_date) from exc

    rates = data.get("rates", {})
    if to_currency not in rates:
        raise FxRateUnavailable(from_currency, to_currency, rate_date)

    return Decimal(str(rates[to_currency]))


async def _store_in_db(
    from_currency: str,
    to_currency: str,
    rate_date: date,
    rate: Decimal,
    session: AsyncSession,
) -> None:
    """Insert rate using ON CONFLICT DO NOTHING for idempotent caching."""
    stmt = pg_insert(FxRate).values(
        from_currency=from_currency,
        to_currency=to_currency,
        rate_date=rate_date,
        rate=rate,
        source="frankfurter",
    ).on_conflict_do_nothing(constraint="uq_fx_rate_date_pair")
    await session.execute(stmt)
    await session.flush()
