from datetime import datetime

from sqlalchemy.orm import Session

from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate
from app.repositories.layers.fundamental_snapshot_repository import FundamentalSnapshotRepository


class FundamentalSnapshotService:
    def __init__(self, db: Session):
        self.repo = FundamentalSnapshotRepository(db)

    def save(self, ticker: str, date_time: datetime, data: dict):
        payload = FundamentalSnapshotCreate(ticker=ticker, as_of_date=date_time, **data)
        return self.repo.create(payload)

    def get_latest(self, ticker: str, date_time: datetime):
        return self.repo.get_latest(ticker, date_time)


