from datetime import datetime

from sqlalchemy.orm import Session

from app.db.schemas.layers.company_news_scheme import CompanyNewsDTO, CompanyNewsCreate
from app.repositories.layers.company_news_repository import CompanyNewsRepository


class CompanyNewsService:
    def __init__(self, db: Session):
        self.repo = CompanyNewsRepository(db)

    def save(self, ticker: str, date_time: datetime, data: dict):
        payload = CompanyNewsCreate(ticker=ticker, as_of_date=date_time, **data)
        obj = self.repo.create(payload)
        return CompanyNewsDTO.model_validate(obj)

    def get_latest(
            self,
            ticker: str,
            date_time: datetime
    ) -> CompanyNewsDTO | None:
        obj = self.repo.get_latest(ticker=ticker, date_time=date_time)

        if obj is None:
            return None

        return CompanyNewsDTO.model_validate(obj)


