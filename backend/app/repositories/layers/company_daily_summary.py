from datetime import timedelta
from operator import and_

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.company_daily_summary import CompanyDailySummary
from app.db.schemas.layers.company_daily_summary import CompanyDailySummaryCreate


class CompanyDailySummaryRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: CompanyDailySummaryCreate):
        obj = CompanyDailySummary(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, ticker: str, date):
        stmt = select(CompanyDailySummary).where(
            CompanyDailySummary.ticker == ticker,
            CompanyDailySummary.date == date
        )

        return self.db.execute(stmt).scalar_one_or_none()

    def get_news_for_period(self, ticker: str, target_date, days_limit: int):
        start_date = target_date - timedelta(days=days_limit)

        stmt = (
            select(CompanyDailySummary)
            .where(
                CompanyDailySummary.ticker == ticker,
                CompanyDailySummary.date <= target_date,
                CompanyDailySummary.date >= start_date
            )
            .order_by(CompanyDailySummary.date.desc())
        )

        result = self.db.execute(stmt)
        return result.scalars().all()