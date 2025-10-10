from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.db.database import get_db
from datetime import datetime

from app.services.portfolio_valuation_service import PortfolioValuationService

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


def get_service(db: Session):
    return PortfolioService(db, PortfolioValuationService(MarketDataService(db)))


# ---- 1️⃣ Historia z bazy ----
@router.get("/{portfolio_id}/history")
def get_portfolio_history(
    portfolio_id: int,
    detailed: bool = Query(True, description="Czy zwrócić szczegółową historię?"),
    db: Session = Depends(get_db)
):
    service = get_service(db)
    history = service.get_portfolio_history(portfolio_id, detailed)
    if not history:
        raise HTTPException(status_code=404, detail="No history for this portfolio")
    return history


# ---- 2️⃣ Symulowana wycena (valuation) ----
@router.get("/{portfolio_id}/valuation")
def get_portfolio_valuation(
    portfolio_id: int,
    start: datetime = Query(..., description="Początek zakresu dat"),
    end: datetime = Query(..., description="Koniec zakresu dat"),
    interval: Literal["1h", "4h", "1d", "1w"] = Query("1h", description="Interwał czasowy"),
    detailed: bool = Query(False, description="Czy zwrócić szczegółową historię?"),
    db: Session = Depends(get_db)
):
    service = get_service(db)
    return service.get_portfolio_valuation_in_range(portfolio_id, start, end, interval, detailed)


# ---- Stan portfela na dany dzień ----
@router.get("/{portfolio_id}/state")
def get_portfolio_state_on_date(
    portfolio_id: int,
    date: datetime = Query(..., description="Data w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db),
    detailed: bool = Query(False, description="Czy zwrócić szczegółowe informacje?")
):
    service = get_service(db)
    state = service.compute_portfolio_state_at_date(portfolio_id, date, detailed)
    if not state:
        raise HTTPException(status_code=404, detail="No state for given date")
    return state


