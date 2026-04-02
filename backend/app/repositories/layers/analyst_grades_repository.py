from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.analyst_grades import AnalystGrades
from app.db.schemas.layers.analyst_grades_scheme import AnalystGradesCreate


class AnalystGradesRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AnalystGradesCreate) -> AnalystGrades | None:
        obj = AnalystGrades(**data.dict())
        self.db.add(obj)

        try:
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except IntegrityError:
            self.db.rollback()
            return None  # rekord już istnieje

    def get_latest(self, ticker: str, date_time: datetime, limit: int = 1):
        return (
            self.db.query(AnalystGrades)
            .filter(
                AnalystGrades.ticker == ticker,
                AnalystGrades.as_of_date <= date_time
            )
            .order_by(AnalystGrades.as_of_date.desc())
            .limit(limit)
            .all()
        )


