from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.db.models.market_data import MarketData
from app.db.schemas.market_data import MarketDataCreate

class MarketDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: MarketDataCreate) -> MarketData:
        if isinstance(data, dict):
            db_obj = MarketData(**data)
        else:
            db_obj = MarketData(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_ticker_until_date(self, ticker: str, date_time: datetime, limit: int = 1):
        return (
            self.db.query(MarketData)
            .filter(
                MarketData.ticker == ticker,
                MarketData.datetime <= date_time
            )
            .order_by(MarketData.datetime.desc())
            .limit(limit)
            .all()
        )

    def get_price_at_date(self, ticker: str, date_time: datetime) -> Optional[MarketData]:
        """
        Pobiera najnowsze dane rynkowe (np. close price) do danego dnia.
        """
        return (
            self.db.query(MarketData)
            .filter(
                MarketData.ticker == ticker,
                MarketData.datetime <= date_time
            )
            .order_by(MarketData.datetime.desc())
            .first()
        )

    def exists_in_range(self, ticker: str, start: datetime, end: datetime) -> bool:
        """
           Sprawdza czy cały zakres od start do end jest pokryty danymi w bazie.
           """
        # Sprawdź czy istnieją dane na początku i na końcu zakresu
        has_start = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime == start
        ).first() is not None

        has_end = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime == end
        ).first() is not None

        return has_start and has_end

