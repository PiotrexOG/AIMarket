from datetime import datetime
from pydantic import BaseModel

class MarketDataBase(BaseModel):
    datetime: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataCreate(MarketDataBase):
    pass


class MarketDataRead(MarketDataBase):
    id: int

    class Config:
        from_attributes = True
