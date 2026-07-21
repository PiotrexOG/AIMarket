from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    archetype_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    top_m_share = Column(Float, nullable=False, default=1.0)
    investment_time_days = Column(Integer, nullable=False, default=300)
    rebalance_time_share = Column(Float, nullable=False, default=0.2)

    user = relationship("User", back_populates="portfolios")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship(
        "PortfolioTransaction",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    cycle_events = relationship(
        "PortfolioCycleEvent",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )


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
    amount = Column(Float, nullable=False)

    portfolio_history = relationship("PortfolioHistory", back_populates="shares")


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    ticker = Column(String, nullable=False)
    type = Column(Enum("BUY", "SELL", name="transaction_type"), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")


class TickerScoreSnapshot(Base):
    __tablename__ = "ticker_score_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "datetime",
            "ticker",
            "timeframe",
            name="uq_ticker_score_snapshots_datetime_ticker_timeframe",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    ticker = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False, default="long_term_200d")
    score = Column(Float, nullable=False)
    score_percentile = Column(Float, nullable=False)


class PortfolioCycleEvent(Base):
    __tablename__ = "portfolio_cycle_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    event_type = Column(
        Enum("START", "RESET", "REBALANCE", name="portfolio_cycle_event_type"),
        nullable=False,
    )
    investment_start_date = Column(DateTime(timezone=True), index=True, nullable=False)
    next_rebalance_date = Column(DateTime(timezone=True), nullable=True)
    next_cycle_date = Column(DateTime(timezone=True), nullable=True)
    investment_time_days = Column(Integer, nullable=False)
    rebalance_time_share = Column(Float, nullable=False)
    selected_tickers = Column(JSON, nullable=False, default=list)
    sold_tickers = Column(JSON, nullable=False, default=list)
    replacement_tickers = Column(JSON, nullable=False, default=list)
    entry_score_percentiles = Column(JSON, nullable=False, default=dict)

    portfolio = relationship("Portfolio", back_populates="cycle_events")
