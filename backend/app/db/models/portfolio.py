from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)

    user = relationship("User", back_populates="portfolios")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")


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
