from datetime import datetime
from statistics import median
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

    def get_window_price(
        self,
        ticker: str,
        date_time: datetime,
        window_positions: int = 2,
    ) -> Optional[float]:
        """
        Zwraca wygladzona cene OHLC4 z okna rekordow wokol timestampu.

        window_positions=2 i side="around" oznacza:
        2 rekordy przed + rekord bazowy <= timestamp + 2 rekordy po.

        """
        rows = self.repo.get_price_window_at_date(
            ticker=ticker,
            date_time=date_time,
            window_positions=window_positions
        )

        values = [
            (row.open + row.high + row.low + row.close) / 4
            for row in rows
            if (
                row.open is not None
                and row.high is not None
                and row.low is not None
                and row.close is not None
            )
        ]

        if not values:
            return None

        return float(median(values))


    def check_data_coverage(self, ticker: str, start: datetime, end: datetime
    ) -> tuple[bool, bool]:
        """
        Sprawdza, czy istnieją dane rynkowe dla danego tickera w podanym zakresie.
        """
        return self.repo.check_data_coverage(ticker, start, end)

    def get_data_range(self, ticker: str):
        """
        Sprawdza, czy istnieją dane rynkowe dla danego tickera w podanym zakresie.
        """
        return self.repo.get_data_range(ticker)

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
            limit = 200 * 7

        df = self.get_recent_df(ticker, date_time, limit)
        if df.empty:
            return {}

        analytical = AnalyticalService()
        df = analytical.compute_all(df, use_daily)

        df = df.round(3)

        last = df.iloc[-1].replace({np.nan: None, np.inf: None, -np.inf: None})
        return last.to_dict()

    def get_prices_for_timestamps(
        self,
        timestamps: list[datetime],
        window_positions: int = 0
    ) -> dict[datetime, dict[str, float]]:
        """
        Dla listy dat zwraca słownik: { timestamp: { ticker: price } }
        """
        all_tickers = self.get_all_tickers().tickers
        results = {}

        for ts in timestamps:
            # Pobieramy najnowsze ceny dla wszystkich tickerów do danego ts włącznie
            # Wykorzystujemy subquery, aby znaleźć max(datetime) dla każdego tickera <= ts
            if window_positions <= 0:
                prices_at_ts = self.repo.get_all_prices_at_date(all_tickers, ts)
            else:
                prices_at_ts = {}

                for ticker in all_tickers:
                    price = self.get_window_price(
                        ticker=ticker,
                        date_time=ts,
                        window_positions=window_positions
                    )

                    if price is not None:
                        prices_at_ts[ticker] = price

            results[ts] = prices_at_ts

        return results
