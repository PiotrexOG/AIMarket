from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config.config import LOCALLY

from app.db.models.base import Base
from app.db.models.user import User
from app.db.models.market_data import MarketData
from app.db.models.fundamental_snapshot import FundamentalSnapshot
from app.db.models.company_daily_summary import CompanyDailySummary
from app.db.models.analyst_grades import AnalystGrades
from app.db.models.portfolio import *



#DATABASE_URL = "postgresql+psycopg2://postgres:postgres@" +  + ":5432/stock_sim"
db = "localhost" if LOCALLY else "postgres"
DATABASE_URL = f"postgresql+psycopg2://postgres:postgres@{db}:5432/stock_sim"

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def reset_database():
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS portfolio_metric_weights"))

    SKIP_TABLES = {
        "market_data",
        "analyst_grades",
        "fundamental_snapshot",
        "company_daily_summary"
    }

    tables_to_drop = [
        t for t in Base.metadata.sorted_tables
        if t.name not in SKIP_TABLES
    ]

    for table in reversed(tables_to_drop):
        table.drop(engine, checkfirst=True)

    Base.metadata.create_all(bind=engine)


def migrate_portfolio_strategy_columns():
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS portfolio_metric_weights"))
        connection.execute(text(
            "ALTER TABLE portfolios "
            "ADD COLUMN IF NOT EXISTS investment_time_days INTEGER NOT NULL DEFAULT 300"
        ))
        connection.execute(text(
            "ALTER TABLE portfolios "
            "ADD COLUMN IF NOT EXISTS rebalance_time_share DOUBLE PRECISION NOT NULL DEFAULT 0.2"
        ))
    Base.metadata.create_all(bind=engine)


# Dependency do FastAPI
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
