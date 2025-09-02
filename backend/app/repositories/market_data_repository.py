from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate

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

    def get_by_ticker(self, ticker: str, limit: int = 100):
        return (
            self.db.query(MarketData)
            .filter(MarketData.ticker == ticker)
            .order_by(MarketData.datetime.desc())
            .limit(limit)
            .all()
        )

    def delete_all(self):
        self.db.query(MarketData).delete()
        self.db.commit()
