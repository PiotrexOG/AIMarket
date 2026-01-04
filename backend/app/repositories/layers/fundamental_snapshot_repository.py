from datetime import datetime

from sqlalchemy.orm import Session
from app.db.models.fundamental_snapshot import FundamentalSnapshot
from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate


class FundamentalSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: FundamentalSnapshotCreate) -> FundamentalSnapshot:
        obj = FundamentalSnapshot(**data.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_latest(self, ticker: str, date_time: datetime):
        return (
            self.db.query(FundamentalSnapshot)
            .filter(
                FundamentalSnapshot.ticker == ticker,
                FundamentalSnapshot.as_of_date <= date_time
            )
            .order_by(FundamentalSnapshot.as_of_date.desc())
            .first()
        )


