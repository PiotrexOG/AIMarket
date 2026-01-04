from datetime import datetime
from pydantic import BaseModel


class FundamentalSnapshotCreate(BaseModel):
    ticker: str
    as_of_date: datetime

    shares_outstanding: int | None = None
    equity: int | None = None
    total_debt: int | None = None
    cash_and_equivalents: int | None = None
    revenue_ttm: int | None = None
    free_cash_flow_ttm: int | None = None

    eps_ttm: float | None = None
    gross_margin_ttm: float | None = None
    operating_margin_ttm: float | None = None
    net_margin_ttm: float | None = None
    revenue_growth_ttm_yoy: float | None = None
    eps_growth_ttm_yoy: float | None = None

