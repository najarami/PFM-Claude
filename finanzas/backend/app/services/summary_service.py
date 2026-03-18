"""Aggregation queries for monthly summaries and comparisons."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction
from app.services.fx_service import FxRateUnavailable, convert_amount, get_rates_bulk


@dataclass
class CategoryBreakdown:
    category_id: str | None
    category_name: str
    category_slug: str
    icon: str
    color: str
    amount: float
    count: int
    pct_of_total: float


@dataclass
class MonthlySummary:
    year: int
    month: int
    total_income: float
    total_expense: float
    net: float
    by_category: list[CategoryBreakdown]
    transaction_count: int
    display_currency: str


async def get_monthly_summary(
    year: int,
    month: int,
    session: AsyncSession,
    currency: str = "CLP",
    mode: str = "native",
) -> MonthlySummary:
    """
    mode='native'    → filter by currency, no conversion (original behavior)
    mode='converted' → fetch all currencies, convert each transaction to `currency`
    """
    if mode == "converted":
        return await _get_summary_converted(year, month, session, target_currency=currency)
    return await _get_summary_native(year, month, session, currency=currency)


async def _get_summary_native(
    year: int, month: int, session: AsyncSession, currency: str
) -> MonthlySummary:
    """Original behavior: filter transactions by currency."""
    base_filter = [
        Transaction.year == year,
        Transaction.month == month,
        Transaction.is_duplicate.is_(False),
        Transaction.currency == currency,
    ]

    income_q = await session.execute(
        select(func.sum(Transaction.amount)).where(
            *base_filter, Transaction.transaction_type == "income"
        )
    )
    expense_q = await session.execute(
        select(func.sum(func.abs(Transaction.amount))).where(
            *base_filter, Transaction.transaction_type.in_(["expense", "transfer"])
        )
    )
    count_q = await session.execute(
        select(func.count(Transaction.id)).where(*base_filter)
    )

    total_income = float(income_q.scalar() or 0)
    total_expense = float(expense_q.scalar() or 0)
    count = int(count_q.scalar() or 0)

    by_cat_q = await session.execute(
        select(
            Transaction.category_id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.color,
            Category.is_income,
            func.sum(func.abs(Transaction.amount)).label("total"),
            func.count(Transaction.id).label("cnt"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filter)
        .group_by(
            Transaction.category_id,
            Category.name, Category.slug, Category.icon, Category.color, Category.is_income,
        )
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
    )
    rows = by_cat_q.all()

    breakdown = []
    for row in rows:
        cat_total = float(row.total)
        base = total_expense if not row.is_income else total_income
        pct = round(cat_total / base * 100, 1) if base > 0 else 0.0
        breakdown.append(CategoryBreakdown(
            category_id=str(row.category_id) if row.category_id else None,
            category_name=row.name or "Sin categoría",
            category_slug=row.slug or "uncategorized",
            icon=row.icon or "📦",
            color=row.color or "#6B7280",
            amount=cat_total,
            count=int(row.cnt),
            pct_of_total=pct,
        ))

    return MonthlySummary(
        year=year,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        net=total_income - total_expense,
        by_category=breakdown,
        transaction_count=count,
        display_currency=currency,
    )


async def _get_summary_converted(
    year: int, month: int, session: AsyncSession, target_currency: str
) -> MonthlySummary:
    """Fetch all transactions for the month and convert each to target_currency."""
    base_filter = [
        Transaction.year == year,
        Transaction.month == month,
        Transaction.is_duplicate.is_(False),
    ]

    # Fetch all transactions with category info
    txs_q = await session.execute(
        select(
            Transaction.id,
            Transaction.amount,
            Transaction.currency,
            Transaction.transaction_type,
            Transaction.date,
            Transaction.category_id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.color,
            Category.is_income,
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filter)
    )
    rows = txs_q.all()

    if not rows:
        return MonthlySummary(
            year=year, month=month,
            total_income=0, total_expense=0, net=0,
            by_category=[], transaction_count=0,
            display_currency=target_currency,
        )

    # Collect unique (from, to, date) pairs for bulk fetch
    pairs = list({
        (row.currency, target_currency, row.date)
        for row in rows
        if row.currency != target_currency
    })
    rates = await get_rates_bulk(pairs, session)

    # Aggregate converted amounts
    total_income = Decimal("0")
    total_expense = Decimal("0")
    cat_totals: dict[str | None, dict] = {}

    for row in rows:
        rate_key = (row.currency, target_currency, row.date)
        if row.currency == target_currency:
            rate = Decimal("1")
        else:
            rate = rates.get(rate_key)
            if rate is None:
                continue  # Skip transactions where rate is unavailable

        raw_amount = Decimal(str(row.amount))
        converted = convert_amount(abs(raw_amount), row.currency, target_currency, rate)

        if row.transaction_type == "income":
            total_income += converted
        else:
            total_expense += converted

        # Category aggregation
        cat_key = str(row.category_id) if row.category_id else None
        if cat_key not in cat_totals:
            cat_totals[cat_key] = {
                "name": row.name or "Sin categoría",
                "slug": row.slug or "uncategorized",
                "icon": row.icon or "📦",
                "color": row.color or "#6B7280",
                "is_income": row.is_income,
                "total": Decimal("0"),
                "count": 0,
            }
        cat_totals[cat_key]["total"] += converted
        cat_totals[cat_key]["count"] += 1

    total_income_f = float(total_income)
    total_expense_f = float(total_expense)

    breakdown = []
    for cat_id, data in sorted(cat_totals.items(), key=lambda x: x[1]["total"], reverse=True):
        cat_total = float(data["total"])
        base = total_expense_f if not data["is_income"] else total_income_f
        pct = round(cat_total / base * 100, 1) if base > 0 else 0.0
        breakdown.append(CategoryBreakdown(
            category_id=cat_id,
            category_name=data["name"],
            category_slug=data["slug"],
            icon=data["icon"],
            color=data["color"],
            amount=cat_total,
            count=data["count"],
            pct_of_total=pct,
        ))

    return MonthlySummary(
        year=year,
        month=month,
        total_income=total_income_f,
        total_expense=total_expense_f,
        net=total_income_f - total_expense_f,
        by_category=breakdown,
        transaction_count=len(rows),
        display_currency=target_currency,
    )


async def get_comparison(
    years_months: list[tuple[int, int]],
    session: AsyncSession,
    currency: str = "CLP",
    mode: str = "native",
) -> list[dict]:
    """Return a list of monthly snapshots for comparison view."""
    snapshots = []
    for year, month in years_months:
        summary = await get_monthly_summary(year, month, session, currency=currency, mode=mode)
        snapshots.append({
            "year": year,
            "month": month,
            "total_income": summary.total_income,
            "total_expense": summary.total_expense,
            "net": summary.net,
            "display_currency": summary.display_currency,
            "by_category": {
                b.category_slug: b.amount for b in summary.by_category
            },
        })
    return snapshots
