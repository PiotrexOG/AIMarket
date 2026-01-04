from sqlalchemy import Column, Integer, DateTime, String, Float, UniqueConstraint, BigInteger

from app.db.models.base import Base

class FundamentalSnapshot(Base):
    __tablename__ = "fundamental_snapshot"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True, nullable=False)
    as_of_date = Column(DateTime(timezone=True), index=True, nullable=False)

    shares_outstanding = Column(BigInteger)
    equity = Column(BigInteger)
    total_debt = Column(BigInteger)
    cash_and_equivalents = Column(BigInteger)
    revenue_ttm = Column(BigInteger)
    free_cash_flow_ttm = Column(BigInteger)

    eps_ttm = Column(Float)
    gross_margin_ttm = Column(Float)
    operating_margin_ttm = Column(Float)
    net_margin_ttm = Column(Float)
    revenue_growth_ttm_yoy = Column(Float)
    eps_growth_ttm_yoy = Column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date"),
    )
