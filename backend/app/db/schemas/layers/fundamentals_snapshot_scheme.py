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
    eps: float | None = None
    eps_est_for_next: float | None = None
    eps_est_from_previous: float | None = None
    gross_margin_ttm: float | None = None
    operating_margin_ttm: float | None = None
    net_margin_ttm: float | None = None
    revenue_growth_ttm_yoy: float | None = None
    eps_growth_ttm_yoy: float | None = None


class FundamentalSnapshotDTO(BaseModel):
    id: int
    ticker: str
    as_of_date: datetime

    shares_outstanding: int | None
    equity: int | None
    total_debt: int | None
    cash_and_equivalents: int | None
    revenue_ttm: int | None
    free_cash_flow_ttm: int | None

    eps_ttm: float | None
    eps: float | None = None
    eps_est_for_next: float | None = None
    eps_est_from_previous: float | None = None
    gross_margin_ttm: float | None
    operating_margin_ttm: float | None
    net_margin_ttm: float | None
    revenue_growth_ttm_yoy: float | None
    eps_growth_ttm_yoy: float | None

    class Config:
        from_attributes = True  # SQLAlchemy → Pydantic
