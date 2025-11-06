from datetime import datetime

from fastapi import APIRouter

from app.services.stock_service import StockService
from app.shared.types import ValuationInterval
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.schemas.portfolio import PortfolioTransactionRead
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
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

@router.get("/tickers")
def get_all_tickers(db: Session = Depends(get_db)):
    """
    Zwraca listę wszystkich unikalnych tickerów dostępnych w bazie.
    """
    service = MarketDataService(db)
    return service.get_all_tickers()