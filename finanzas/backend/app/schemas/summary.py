from typing import Optional
from pydantic import BaseModel


class CategoryBreakdownSchema(BaseModel):
    category_id: Optional[str]
    category_name: str
    category_slug: str
    icon: str
    color: str
    amount: float
    count: int
    pct_of_total: float


class MonthlySummarySchema(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float
    net: float
    by_category: list[CategoryBreakdownSchema]
    transaction_count: int


class MonthComparisonSchema(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float
    net: float
    by_category: dict[str, float]
