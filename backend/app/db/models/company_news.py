from sqlalchemy import Column, Integer, DateTime, String, UniqueConstraint

from app.db.models.base import Base

class CompanyNews(Base):
    __tablename__ = "company_news"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True, nullable=False)
    as_of_date = Column(DateTime(timezone=True), index=True, nullable=False)

    headline = Column(String)
    summary = Column(String)

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date"),
    )
