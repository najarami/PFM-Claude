"""Aggregation queries for monthly summaries and comparisons."""
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction


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


async def get_monthly_summary(year: int, month: int, session: AsyncSession, currency: str = "CLP") -> MonthlySummary:
    # Total income and expense (excluding duplicates, filtered by currency)
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

    # By category breakdown (expenses only for budget purposes)
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
    )


async def get_comparison(years_months: list[tuple[int, int]], session: AsyncSession, currency: str = "CLP") -> list[dict]:
    """Return a list of monthly snapshots for comparison view."""
    snapshots = []
    for year, month in years_months:
        summary = await get_monthly_summary(year, month, session, currency=currency)
        snapshots.append({
            "year": year,
            "month": month,
            "total_income": summary.total_income,
            "total_expense": summary.total_expense,
            "net": summary.net,
            "by_category": {
                b.category_slug: b.amount for b in summary.by_category
            },
        })
    return snapshots
