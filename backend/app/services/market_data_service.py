from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.repositories.market_data_repository import MarketDataRepository
from app.schemas.market_data import MarketDataCreate

class MarketDataService:
    def __init__(self, db: Session):
        self.repo = MarketDataRepository(db)

    def add_market_data(self, data: MarketDataCreate):
        """
        Dodaje nowy rekord danych rynkowych.
        """
        return self.repo.create(data)

    def get_recent_data(self, ticker: str, limit: int = 100):
        """
        Pobiera ostatnie rekordy dla podanego tickera.
        """
        return self.repo.get_by_ticker(ticker, limit)

    def get_price(self, ticker: str, date_time: datetime) -> Optional[float]:
        """
        Zwraca cenę zamknięcia dla danego tickera i daty.
        """
        market_data = self.repo.get_price_at_date(ticker, date_time)
        return market_data.close if market_data else None

    def delete_all(self):
        """
        Usuwa wszystkie rekordy z tabeli MarketData.
        """
        self.repo.delete_all()
