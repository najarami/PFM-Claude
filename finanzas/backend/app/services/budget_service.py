"""Budget management: actual vs budget comparison."""
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction


@dataclass
class BudgetStatus:
    category_id: str
    category_name: str
    category_slug: str
    icon: str
    color: str
    budget_amount: float
    actual_amount: float
    remaining: float
    pct_used: float


async def get_budget_status(year: int, month: int, session: AsyncSession, currency: str = "CLP") -> list[BudgetStatus]:
    """
    Returns budget vs actual for all expense categories that have a budget set.
    Budget resolution: (category, month, year, currency) > (category, month=0, year, currency) > (category, 0, 0, currency)
    Filters both budget amounts and actual spending by currency.
    """
    # Get all expense categories
    cats_q = await session.execute(
        select(Category).where(Category.is_income.is_(False)).order_by(Category.sort_order)
    )
    categories = cats_q.scalars().all()

    statuses = []
    for cat in categories:
        # Find most specific budget for this currency
        budget_amount = await _resolve_budget(cat.id, month, year, session, currency=currency)
        if budget_amount is None:
            continue  # no budget set for this category + currency

        # Actual spending this month filtered by currency
        actual_q = await session.execute(
            select(func.sum(func.abs(Transaction.amount))).where(
                Transaction.category_id == cat.id,
                Transaction.year == year,
                Transaction.month == month,
                Transaction.is_duplicate.is_(False),
                Transaction.transaction_type.in_(["expense", "transfer"]),
                Transaction.currency == currency,
            )
        )
        actual = float(actual_q.scalar() or 0)
        remaining = budget_amount - actual
        pct_used = round(actual / budget_amount * 100, 1) if budget_amount > 0 else 0.0

        statuses.append(BudgetStatus(
            category_id=str(cat.id),
            category_name=cat.name,
            category_slug=cat.slug,
            icon=cat.icon or "📦",
            color=cat.color or "#6B7280",
            budget_amount=budget_amount,
            actual_amount=actual,
            remaining=remaining,
            pct_used=pct_used,
        ))

    return statuses


async def _resolve_budget(
    category_id, month: int, year: int, session: AsyncSession, currency: str = "CLP"
) -> float | None:
    """Priority: specific month/year > month only > global default (0/0), all for the same currency."""
    for m, y in [(month, year), (month, 0), (0, 0)]:
        result = await session.execute(
            select(Budget.amount).where(
                Budget.category_id == category_id,
                Budget.month == m,
                Budget.year == y,
                Budget.currency == currency,
            ).limit(1)
        )
        val = result.scalar_one_or_none()
        if val is not None:
            return float(val)
    return None


async def upsert_budget(
    category_slug: str, amount: float, month: int, year: int, session: AsyncSession, currency: str = "CLP"
) -> Budget:
    """Create or update budget for a category + currency combination."""
    cat_q = await session.execute(
        select(Category.id).where(Category.slug == category_slug)
    )
    cat_id = cat_q.scalar_one_or_none()
    if cat_id is None:
        raise ValueError(f"Category '{category_slug}' not found")

    existing_q = await session.execute(
        select(Budget).where(
            Budget.category_id == cat_id,
            Budget.month == month,
            Budget.year == year,
            Budget.currency == currency,
        ).limit(1)
    )
    existing = existing_q.scalar_one_or_none()

    if existing:
        existing.amount = amount
        await session.commit()
        return existing

    budget = Budget(category_id=cat_id, month=month, year=year, currency=currency, amount=amount)
    session.add(budget)
    await session.commit()
    return budget
