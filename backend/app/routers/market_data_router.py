from app.services.stock_service import StockService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.services.layers.market_data_service import MarketDataService
from app.db.database import get_db
from datetime import datetime
from app.shared.types import ValuationInterval

router = APIRouter(prefix="/market-data", tags=["MarketData"])

@router.get("/{ticker}/valuation")
def get_stock_valuation(
    ticker: str,
    start: datetime = Query(..., description="Początek zakresu dat"),
    end: datetime = Query(..., description="Koniec zakresu dat"),
    interval: ValuationInterval = Query("1h", description="Interwał czasowy"),
    db: Session = Depends(get_db)
):
    service = StockService(db)
    return service.get_stock_valuation_in_range(ticker, start, end, interval)

@router.get("/{ticker}/indicators")
def get_stock_indicators(
    ticker: str,
    use_daily: bool,
    date_time: datetime = Query(..., description="Data"),
    db: Session = Depends(get_db)
):
    service = MarketDataService(db)
    return service.get_indicators(ticker, date_time, use_daily=use_daily)

@router.get("/tickers")
def get_all_tickers(db: Session = Depends(get_db)):
    """
    Zwraca listę wszystkich unikalnych tickerów dostępnych w bazie.
    """
    service = MarketDataService(db)
    return service.get_all_tickers()