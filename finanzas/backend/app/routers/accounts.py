from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(tags=["accounts"])


@router.get("/accounts", response_model=list[AccountRead])
async def list_accounts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Account).order_by(Account.created_at))
    return result.scalars().all()


@router.post("/accounts", response_model=AccountRead, status_code=201)
async def create_account(body: AccountCreate, session: AsyncSession = Depends(get_session)):
    account = Account(**body.model_dump())
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account
