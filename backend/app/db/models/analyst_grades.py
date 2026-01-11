from sqlalchemy import Column, Integer, DateTime, String, UniqueConstraint

from app.db.models.base import Base

class AnalystGrades(Base):
    __tablename__ = "analyst_grades"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True, nullable=False)
    as_of_date = Column(DateTime(timezone=True), index=True, nullable=False)

    analystRatingsStrongBuy = Column(Integer)
    analystRatingsBuy = Column(Integer)
    analystRatingsHold = Column(Integer)
    analystRatingsSell = Column(Integer)
    analystRatingsStrongSell = Column(Integer)

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date"),
    )
