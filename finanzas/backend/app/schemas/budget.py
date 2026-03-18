from pydantic import BaseModel


class BudgetStatusSchema(BaseModel):
    category_id: str
    category_name: str
    category_slug: str
    icon: str
    color: str
    budget_amount: float
    actual_amount: float
    remaining: float
    pct_used: float


class BudgetWrite(BaseModel):
    amount: float
    month: int = 0       # 0 = default for all months
    year: int = 0        # 0 = default for all years
    currency: str = "CLP"  # CLP or USD
