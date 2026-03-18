"""Two-phase deduplication service."""
import hashlib
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction

CREDIT_CARD_PAYMENT_KEYWORDS = [
    "PAGO TARJETA", "PAGO TC", "PAG TC", "PAGO CREDITO",
    "TRANSFERENCIA A TARJETA", "PAGO VISA", "PAGO MASTERCARD",
    "PAG. TARJETA", "PAGO DE TARJETA",
]


def compute_dedup_hash(account_id: str, date, amount: Decimal, description: str) -> str:
    """SHA-256 of account+date+amount+normalized description for exact-match dedup."""
    payload = f"{account_id}|{date.isoformat()}|{amount}|{description.upper().strip()}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def find_exact_duplicate(session: AsyncSession, dedup_hash: str) -> Transaction | None:
    """Return existing non-duplicate transaction with the same hash, or None."""
    result = await session.execute(
        select(Transaction)
        .where(Transaction.dedup_hash == dedup_hash, Transaction.is_duplicate.is_(False))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def find_cross_account_duplicate(
    session: AsyncSession,
    amount: Decimal,
    date,
    account_id: str,
    description: str,
) -> Transaction | None:
    """
    Detect credit card payment duplicated across checking + credit card accounts.

    Conditions:
    - Different account
    - Absolute amount matches within 1 CLP
    - Date within ±3 days
    - Either this or the other transaction has a payment keyword in description
    """
    has_payment_keyword = any(kw in description.upper() for kw in CREDIT_CARD_PAYMENT_KEYWORDS)
    if not has_payment_keyword:
        return None

    date_min = date - timedelta(days=3)
    date_max = date + timedelta(days=3)
    abs_amount = abs(amount)

    result = await session.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.account_id != account_id,
                Transaction.date >= date_min,
                Transaction.date <= date_max,
                func.abs(Transaction.amount) >= abs_amount - 1,
                func.abs(Transaction.amount) <= abs_amount + 1,
                Transaction.is_duplicate.is_(False),
                or_(
                    *[Transaction.description.contains(kw) for kw in CREDIT_CARD_PAYMENT_KEYWORDS]
                ),
            )
        )
        .limit(1)
    )
    return result.scalar_one_or_none()
