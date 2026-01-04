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

    def exists_in_range(self, ticker: str, start: datetime, end: datetime) -> bool:
        """
        Sprawdza czy cały zakres od start do end jest pokryty danymi w bazie.
        Dla końca zakresu akceptuje również dane z 1 godziną wcześniej.
        """
        # Sprawdź czy istnieją dane na początku zakresu
        has_start = self.db.query(MarketData.id).filter(
            MarketData.ticker == ticker,
            MarketData.datetime == start
        ).first() is not None

        # Sprawdź czy istnieją dane na końcu zakresu LUB 1 godzinę wcześniej
        end_minus_1h = end - timedelta(hours=1)
        has_end = (
                self.db.query(MarketData.id).filter(
                    MarketData.ticker == ticker,
                    MarketData.datetime == end
                ).first() is not None
                or
                self.db.query(MarketData.id).filter(
                    MarketData.ticker == ticker,
                    MarketData.datetime == end_minus_1h
                ).first() is not None
        )
        #return True
        return has_start and has_end

    def get_unique_tickers(self) -> list[str]:
        """
        Zwraca listę unikalnych tickerów z tabeli market_data.
        """
        results = self.db.query(MarketData.ticker).distinct().all()
        return [r[0] for r in results]