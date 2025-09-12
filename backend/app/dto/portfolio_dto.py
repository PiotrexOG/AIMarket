from datetime import datetime
from typing import List

from pydantic import BaseModel

class PositionDetail(BaseModel):
    ticker: str
    shares: int
    price: float
    value: float

class PortfolioStateDTO(BaseModel):
    user_id: int
    date: str
    cash: float
    portfolio_value: float
    positions: List[PositionDetail]

class PortfolioSummaryDTO(BaseModel):
    date: str
    portfolio_value: float

class PortfolioValuation(BaseModel):
    date: datetime
    cash: float
    portfolio_value: float
    positions: List[PositionDetail]
