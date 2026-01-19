from datetime import datetime

from sqlalchemy.orm import Session

from app.db.schemas.layers.analyst_grades_scheme import AnalystGradesCreate, AnalystGradesDTO
from app.repositories.layers.analyst_grades_repository import AnalystGradesRepository



class AnalystGradesService:
    def __init__(self, db: Session):
        self.repo = AnalystGradesRepository(db)

    def save(self, ticker: str, date_time: datetime, data: dict):
        payload = AnalystGradesCreate(ticker=ticker, as_of_date=date_time, **data)
        obj = self.repo.create(payload)
        return AnalystGradesDTO.model_validate(obj)

    from typing import List, Optional

    def get_latest(
            self,
            ticker: str,
            date_time: datetime,
            limit: int = 1
    ) -> Optional[List[AnalystGradesDTO]]:
        objs = self.repo.get_latest(ticker=ticker, date_time=date_time, limit=limit)

        if not objs:
            return None

        return [AnalystGradesDTO.model_validate(obj) for obj in objs]


