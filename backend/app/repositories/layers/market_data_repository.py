from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import func, and_
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

    def check_data_coverage(
            self, ticker: str, start: datetime, end: datetime, tolerance_days: int = 4
    ) -> tuple[bool, bool]:
        """
        Zwraca:
        (has_start, has_end)
        """

        has_start = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime >= start - timedelta(days=tolerance_days),
            MarketData.datetime <= start + timedelta(days=tolerance_days)
        ).first() is not None

        has_end = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime >= end - timedelta(days=tolerance_days),
            MarketData.datetime <= end + timedelta(days=tolerance_days)
        ).first() is not None

        return has_start, has_end

    def get_data_range(self, ticker: str):
        result = self.db.query(
            func.min(MarketData.datetime),
            func.max(MarketData.datetime)
        ).filter(
            MarketData.ticker == ticker
        ).first()

        return result  # (min_date, max_date)

    def get_unique_tickers(self) -> list[str]:
        """
        Zwraca listę unikalnych tickerów z tabeli market_data.
        """
        results = self.db.query(MarketData.ticker).distinct().all()
        return [r[0] for r in results]

    def get_all_prices_at_date(self, tickers: list[str], date_time: datetime) -> dict[str, float]:
        """
        Zwraca słownik { ticker: close_price } dla podanej listy tickerów
        według stanu na podany moment (najświeższa cena <= date_time).
        """
        # 1. Znajdujemy najświeższy timestamp dla każdego tickera
        subquery = (
            self.db.query(
                MarketData.ticker,
                func.max(MarketData.datetime).label("max_dt")
            )
            .filter(
                MarketData.ticker.in_(tickers),
                MarketData.datetime <= date_time
            )
            .group_by(MarketData.ticker)
            .subquery()
        )

        # 2. Joinujemy z tabelą główną, aby wyciągnąć cenę 'close' dla tych timestampów
        rows = (
            self.db.query(MarketData.ticker, MarketData.close)
            .join(
                subquery,
                and_(
                    MarketData.ticker == subquery.c.ticker,
                    MarketData.datetime == subquery.c.max_dt
                )
            )
            .all()
        )

        return {row.ticker: row.close for row in rows}