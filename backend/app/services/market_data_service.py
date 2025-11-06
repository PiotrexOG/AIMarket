from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.repositories.market_data_repository import MarketDataRepository
from app.db.schemas.market_data import MarketDataCreate, TickerListDTO


class MarketDataService:
    def __init__(self, db: Session):
        self.repo = MarketDataRepository(db)

    def add_market_data(self, data: MarketDataCreate):
        """
        Dodaje nowy rekord danych rynkowych.
        """
        return self.repo.create(data)

    def get_recent_data(self, ticker: str, date_time: datetime, limit: int = 1):
        """
        Pobiera ostatnie rekordy dla podanego tickera do wskazanej daty.
        """
        return self.repo.get_by_ticker_until_date(ticker, date_time, limit)

    def get_price(self, ticker: str, date_time: datetime) -> Optional[float]:
        """
        Zwraca cenę zamknięcia dla danego tickera i daty.
        """
        market_data = self.repo.get_price_at_date(ticker, date_time)
        return market_data.close if market_data else None

    def has_data_in_range(self, ticker: str, start: datetime, end: datetime) -> bool:
        """
        Sprawdza, czy istnieją dane rynkowe dla danego tickera w podanym zakresie.
        """
        return self.repo.exists_in_range(ticker, start, end)

    def get_all_tickers(self) -> TickerListDTO:
        """
        Zwraca listę wszystkich unikalnych tickerów.
        """
        tickers = self.repo.get_unique_tickers()
        return TickerListDTO(tickers=tickers)


