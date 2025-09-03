from datetime import datetime
from typing import List
from pydantic import BaseModel


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
    total_value: float


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
