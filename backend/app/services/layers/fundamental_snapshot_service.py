from datetime import datetime

from sqlalchemy.orm import Session

from app.db.schemas.layers.fundamentals_snapshot_scheme import FundamentalSnapshotCreate, FundamentalSnapshotDTO
from app.repositories.layers.fundamental_snapshot_repository import FundamentalSnapshotRepository


class FundamentalSnapshotService:
    def __init__(self, db: Session):
        self.repo = FundamentalSnapshotRepository(db)

    def save(self, ticker: str, date_time: datetime, data: dict):
        payload = FundamentalSnapshotCreate(ticker=ticker, as_of_date=date_time, **data)
        obj = self.repo.create(payload)
        return FundamentalSnapshotDTO.model_validate(obj)

    def get_latest(
            self,
            ticker: str,
            date_time: datetime
    ) -> FundamentalSnapshotDTO | None:
        obj = self.repo.get_latest(ticker=ticker, date_time=date_time)

        if obj is None:
            return None

        return FundamentalSnapshotDTO.model_validate(obj)


