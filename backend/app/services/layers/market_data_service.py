from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.layers.market_data_repository import MarketDataRepository
from app.db.schemas.layers.market_data_scheme import MarketDataCreate, TickerListDTO
from app.services.layers.analytical_service import AnalyticalService


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

    def get_recent_df(self, ticker: str, date_time: datetime, limit: int = 200) -> pd.DataFrame:
        """
        Pobiera dane OHLCV z bazy i konwertuje do DataFrame.
        """
        rows = self.repo.get_by_ticker_until_date(ticker, date_time, limit)

        if not rows:
            return pd.DataFrame()

        data = [{
            "Datetime": row.datetime,
            "Open": row.open,
            "High": row.high,
            "Low": row.low,
            "Close": row.close,
            "Volume": row.volume,
            "Ticker": row.ticker
        } for row in rows]

        df = pd.DataFrame(data)
        df = df.sort_values("Datetime")
        df.reset_index(drop=True, inplace=True)

        return df

    def get_indicators(self, ticker: str, date_time: datetime, use_daily=True) -> pd.DataFrame:
        limit = 200
        if use_daily:
            limit = 200 * 8

        df = self.get_recent_df(ticker, date_time, limit)
        if df.empty:
            return {}

        analytical = AnalyticalService()
        df = analytical.compute_all(df, use_daily)

        df = df.round(3)

        last = df.iloc[-1].replace({np.nan: None, np.inf: None, -np.inf: None})
        return last.to_dict()



