from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.base import Base

#DATABASE_URL = "postgresql+psycopg2://postgres:postgres@postgres:5432/stock_sim"
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/stock_sim"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Usuń wszystkie tabele
Base.metadata.drop_all(bind=engine)

# Tworzymy wszystkie tabele
Base.metadata.create_all(bind=engine)

# Dependency do FastAPI
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
