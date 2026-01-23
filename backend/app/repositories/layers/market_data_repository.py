from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from app.db.models.market_data import MarketData
from app.db.schemas.layers.market_data_scheme import MarketDataCreate

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

    def bulk_create(self, data_list: List[MarketDataCreate]):
        """Szybki zapis wielu rekordów naraz."""
        db_objs = [MarketData(**(d if isinstance(d, dict) else d.dict())) for d in data_list]
        self.db.add_all(db_objs)
        self.db.commit()

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

    def exists_in_range(self, ticker: str, start: datetime, end: datetime, tolerance_days: int = 4) -> bool:
        """
        Sprawdza, czy w bazie istnieją dane blisko punktu startowego i końcowego.
        tolerance_days: jak daleko od daty możemy szukać (domyślnie 4 dni, by pokryć długie weekendy).
        """

        # 1. Szukamy najbliższego rekordu w oknie [start - tol, start + tol]
        # To załatwia problem świąt, weekendów i zmian godzin otwarcia.
        has_start = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime >= start - timedelta(days=tolerance_days),
            MarketData.datetime <= start + timedelta(days=tolerance_days)
        ).first() is not None

        if not has_start:
            return False

        # 2. Szukamy najbliższego rekordu w oknie [end - tol, end + tol]
        has_end = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime >= end - timedelta(days=tolerance_days),
            MarketData.datetime <= end + timedelta(days=tolerance_days)
        ).first() is not None

        return has_end

    def get_unique_tickers(self) -> list[str]:
        """
        Zwraca listę unikalnych tickerów z tabeli market_data.
        """
        results = self.db.query(MarketData.ticker).distinct().all()
        return [r[0] for r in results]