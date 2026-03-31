from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.repositories.layers.company_daily_summary import CompanyDailySummaryRepository
from app.db.schemas.layers.company_daily_summary import (
    CompanyDailySummaryCreate,
    CompanyDailySummaryDTO
)


class CompanyDailySummaryService:

    def __init__(self, db: Session):
        self.repo = CompanyDailySummaryRepository(db)

    def save(
        self,
        ticker: str,
        date: date,
        summary: str | None,
        importance: float
    ) -> CompanyDailySummaryDTO:

        payload = CompanyDailySummaryCreate(
            ticker=ticker,
            date=date,
            summary=summary,
            importance=importance,
        )

        obj = self.repo.create(payload)

        return CompanyDailySummaryDTO.model_validate(obj)

    def get(
        self,
        ticker: str,
        date: date
    ) -> CompanyDailySummaryDTO | None:

        obj = self.repo.get(ticker, date)

        if obj is None:
            return None

        return CompanyDailySummaryDTO.model_validate(obj)

    def get_news_window(
            self,
            ticker: str,
            target_date: date,
            days_limit: int
    ) -> list[CompanyDailySummaryDTO]:
        max_allowed_date = target_date - timedelta(days=1)

        news_items = self.repo.get_news_for_period(ticker, max_allowed_date, days_limit)

        return [CompanyDailySummaryDTO.model_validate(obj) for obj in news_items]