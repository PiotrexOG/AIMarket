from sqlalchemy import Column, Integer, Date, String, UniqueConstraint, Float

from app.db.models.base import Base


class CompanyDailySummary(Base):
    __tablename__ = "company_daily_summary"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    summary = Column(String)

    importance = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("ticker", "date"),
    )