from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    archetype_key = Column(String, nullable=False)
    name = Column(String, nullable=False)

    short_term_weight = Column(Float)
    medium_term_weight = Column(Float)
    long_term_weight = Column(Float)
    metric_weights = relationship(
        "PortfolioMetricWeight",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="joined"  # Automatycznie ładuj wagi przy pobieraniu portfela
    )
    risk_tolerance = Column(Float)
    rebalance_threshold = Column(Float)
    min_score_threshold = Column(Float)
    softmax_temp = Column(Float)

    user = relationship("User", back_populates="portfolios")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship(
        "PortfolioTransaction",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )

class PortfolioMetricWeight(Base):
    __tablename__ = "portfolio_metric_weights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # np. "revenue_growth"
    weight = Column(Float, nullable=False)        # np. 0.5

    portfolio = relationship("Portfolio", back_populates="metric_weights")


class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    cash = Column(Float)

    portfolio = relationship("Portfolio", back_populates="history")
    shares = relationship("PortfolioShare", back_populates="portfolio_history", cascade="all, delete-orphan")


class PortfolioShare(Base):
    __tablename__ = "portfolio_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_history_id = Column(Integer, ForeignKey("portfolio_history.id"), nullable=False)
    ticker = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)

    portfolio_history = relationship("PortfolioHistory", back_populates="shares")


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    ticker = Column(String, nullable=False)
    type = Column(Enum("BUY", "SELL", name="transaction_type"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")

