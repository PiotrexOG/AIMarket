from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.company_news import CompanyNews
from app.db.schemas.layers.company_news_scheme import CompanyNewsCreate


class CompanyNewsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CompanyNewsCreate) -> CompanyNews:
        obj = CompanyNews(**data.dict())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_latest(self, ticker: str, date_time: datetime):
        return (
            self.db.query(CompanyNews)
            .filter(
                CompanyNews.ticker == ticker,
                CompanyNews.as_of_date <= date_time
            )
            .order_by(CompanyNews.as_of_date.desc())
            .first()
        )


