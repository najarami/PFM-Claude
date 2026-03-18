"""Upload orchestration: parse → deduplicate → categorize → save."""
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.upload_log import UploadLog
from app.parsers.registry import detect_parser
from app.parsers.base import ParseError
from app.services.category_service import auto_categorize, get_category_id_by_slug
from app.services.dedup_service import (
    compute_dedup_hash,
    find_cross_account_duplicate,
    find_exact_duplicate,
)


class UploadResult:
    def __init__(self):
        self.total_parsed = 0
        self.inserted = 0
        self.duplicates = 0
        self.errors: list[str] = []
        self.upload_log_id: str | None = None


async def process_upload(
    filename: str,
    content: bytes,
    account_id: str,
    session: AsyncSession,
) -> UploadResult:
    result = UploadResult()

    try:
        parser = detect_parser(filename, content)
    except ParseError as e:
        result.errors.append(str(e))
        return result

    log = UploadLog(
        account_id=uuid.UUID(account_id),
        filename=filename,
        file_type="pdf" if filename.lower().endswith(".pdf") else "csv",
        bank=parser.bank.value,
        parser_used=parser.__class__.__name__,
        status="pending",
    )
    session.add(log)
    await session.flush()  # get log.id before transactions reference it

    try:
        raw_txs = parser.parse(io.BytesIO(content), filename)
    except ParseError as e:
        log.status = "error"
        log.error_message = str(e)
        await session.commit()
        result.errors.append(str(e))
        return result

    result.total_parsed = len(raw_txs)

    for raw in raw_txs:
        dedup_hash = compute_dedup_hash(account_id, raw.date, raw.amount, raw.description)

        # Phase 1: exact duplicate check
        existing = await find_exact_duplicate(session, dedup_hash)
        if existing:
            result.duplicates += 1
            continue

        # Resolve category
        category_id = None
        is_auto_cat = False
        category_slug = await auto_categorize(raw.description, session)
        if category_slug:
            cat_id_str = await get_category_id_by_slug(category_slug, session)
            if cat_id_str:
                category_id = uuid.UUID(cat_id_str)
                is_auto_cat = True

        tx = Transaction(
            account_id=uuid.UUID(account_id),
            upload_log_id=log.id,
            date=raw.date,
            description=raw.description,
            raw_description=raw.raw_description,
            amount=float(raw.amount),
            currency=raw.currency,
            transaction_type=raw.transaction_type,
            category_id=category_id,
            is_auto_categorized=is_auto_cat,
            dedup_hash=dedup_hash,
            month=raw.date.month,
            year=raw.date.year,
            source_file=raw.source_file,
        )
        session.add(tx)
        await session.flush()

        # Phase 2: cross-account duplicate check (credit card payments)
        cross = await find_cross_account_duplicate(
            session, raw.amount, raw.date, account_id, raw.description
        )
        if cross:
            tx.is_duplicate = True
            tx.duplicate_of = cross.id
            result.duplicates += 1
        else:
            result.inserted += 1

    log.rows_parsed = result.total_parsed
    log.rows_inserted = result.inserted
    log.rows_duplicate = result.duplicates
    log.status = "success"
    result.upload_log_id = str(log.id)

    await session.commit()
    return result
