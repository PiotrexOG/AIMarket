from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class PortfolioShareBase(BaseModel):
    ticker: str
    amount: float


class PortfolioShareCreate(PortfolioShareBase):
    pass


class PortfolioShareRead(PortfolioShareBase):
    id: int

    class Config:
        from_attributes = True


class PortfolioHistoryBase(BaseModel):
    datetime: datetime
    cash: float


class PortfolioHistoryCreate(PortfolioHistoryBase):
    shares: List[PortfolioShareCreate]


class PortfolioHistoryRead(PortfolioHistoryBase):
    id: int
    shares: List[PortfolioShareRead]

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    name: str
    archetype_key: str
    top_m_share: float = 1.0
    investment_time_days: int = 300
    rebalance_time_share: float = 0.2


class PortfolioCreate(PortfolioBase):
    user_id: int


class PortfolioRead(PortfolioBase):
    id: int
    history: List[PortfolioHistoryRead] = []

    class Config:
        from_attributes = True


class PortfolioTransactionRead(BaseModel):
    datetime: datetime
    decision: str = Field(alias="type")
    ticker: str
    quantity: float
    price: float
    total_value: float

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PortfolioTickerTransactionRead(BaseModel):
    datetime: datetime
    quantity: float
    ratio: float
    price: float
    total_value: float

    model_config = {
        "from_attributes": True,
    }


class TickerScoreSnapshotCreate(BaseModel):
    datetime: datetime
    ticker: str
    timeframe: str = "long_term_200d"
    score: float
    score_percentile: float


class TickerScoreSnapshotRead(TickerScoreSnapshotCreate):
    id: int

    model_config = {
        "from_attributes": True,
    }


class PortfolioCycleEventCreate(BaseModel):
    datetime: datetime
    event_type: str
    investment_start_date: datetime
    next_rebalance_date: datetime | None = None
    next_cycle_date: datetime | None = None
    investment_time_days: int
    rebalance_time_share: float
    selected_tickers: List[str] = []
    sold_tickers: List[str] = []
    replacement_tickers: List[str] = []
    entry_score_percentiles: Dict[str, float] = {}


class PortfolioCycleEventRead(PortfolioCycleEventCreate):
    id: int
    portfolio_id: int

    model_config = {
        "from_attributes": True,
    }
