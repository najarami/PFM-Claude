import uuid
from datetime import datetime
from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    bank: str
    account_type: str  # checking | credit_card | digital_wallet
    currency: str = "CLP"


class AccountRead(BaseModel):
    id: uuid.UUID
    name: str
    bank: str
    account_type: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
