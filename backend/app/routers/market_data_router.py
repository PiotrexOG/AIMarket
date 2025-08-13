from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.schemas.market_data import MarketDataCreate, MarketDataRead
from app.services.market_data_service import MarketDataService
from app.database import get_db

router = APIRouter(prefix="/market-data", tags=["MarketData"])

@router.post("/", response_model=MarketDataRead)
def add_market_data(data: MarketDataCreate, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    return service.add_market_data(data)

@router.get("/{ticker}", response_model=List[MarketDataRead])
def get_recent_data(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    return service.get_recent_data(ticker, limit)
