from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


# ---- Portfolio Share ----
class PortfolioShareBase(BaseModel):
    ticker: str
    amount: float


class PortfolioShareCreate(PortfolioShareBase):
    pass


class PortfolioShareRead(PortfolioShareBase):
    id: int

    class Config:
        from_attributes = True


# ---- Portfolio History ----
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


# ---- Portfolio ----
class PortfolioBase(BaseModel):
    name: str


class PortfolioCreate(PortfolioBase):
    user_id: int


class PortfolioRead(PortfolioBase):
    id: int
    history: List[PortfolioHistoryRead] = []

    class Config:
        from_attributes = True


class PortfolioTransactionRead(BaseModel):
    datetime: datetime
    decision: str = Field(alias="type")  # mapujemy kolumnę SQLAlchemy 'type' → API 'decision'
    ticker: str
    quantity: float
    price: float
    total_value: float

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,  # pozwala aliasom działać dwukierunkowo
    }

class PortfolioTickerTransactionRead(BaseModel):
    datetime: datetime
    quantity: float  # ze znakiem
    ratio: float     # (total_value / portfolio_total_value) ze znakiem

    model_config = {
        "from_attributes": True,
    }
