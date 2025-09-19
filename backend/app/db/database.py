from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import DEBUG_RESET, LOCALLY
from app.db.models.base import Base

#DATABASE_URL = "postgresql+psycopg2://postgres:postgres@" +  + ":5432/stock_sim"
db = "localhost" if LOCALLY else "postgres"
DATABASE_URL = f"postgresql+psycopg2://postgres:postgres@{db}:5432/stock_sim"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

if DEBUG_RESET:
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != "market_data":
            table.drop(engine)
Base.metadata.create_all(bind=engine)


# Dependency do FastAPI
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
