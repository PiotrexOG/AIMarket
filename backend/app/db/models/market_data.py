from sqlalchemy import Column, Integer, DateTime, String, Float, UniqueConstraint
from .base import Base

class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    ticker = Column(String, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "datetime"),
    )
