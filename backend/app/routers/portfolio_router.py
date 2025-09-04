from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioHistoryCreate
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.database import get_db
from datetime import datetime

from app.services.portfolio_valuation_service import PortfolioValuationService

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

# ---- Historia całego portfela (pełna) ----
@router.get("/{portfolio_id}/history")
def get_portfolio_history(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio_valuation_service = PortfolioValuationService(MarketDataService(db))
    portfolio_service = PortfolioService(db, portfolio_valuation_service)
    history = portfolio_service.get_portfolio_history(portfolio_id)
    if not history:
        raise HTTPException(status_code=404, detail="No history for this portfolio")
    return history

# ---- Historia uproszczona (tylko datetime + total_value) ----
@router.get("/{portfolio_id}/history/summary")
def get_portfolio_history_summary(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio_valuation_service = PortfolioValuationService(MarketDataService(db))
    portfolio_service = PortfolioService(db, portfolio_valuation_service)
    return portfolio_service.get_portfolio_summary(portfolio_id)


# ---- Stan portfela na dany dzień (po portfolio_id) ----
@router.get("/{portfolio_id}/state")
def get_portfolio_state_on_date(
    portfolio_id: int,
    date: datetime = Query(..., description="Data w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    portfolio_valuation_service = PortfolioValuationService(MarketDataService(db))
    portfolio_service = PortfolioService(db, portfolio_valuation_service)
    state = portfolio_service.get_portfolio_state(portfolio_id, date)
    if not state:
        raise HTTPException(status_code=404, detail="No state for given date")
    return state

