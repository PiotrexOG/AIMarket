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
    service = PortfolioService(db)
    history = service.get_portfolio_history(portfolio_id)
    if not history:
        raise HTTPException(status_code=404, detail="No history for this portfolio")
    return history


@router.get("/user/{user_id}/history")
def get_user_portfolio_history(user_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    portfolio = service.get_user_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for user")
    return service.get_portfolio_history(portfolio.id)


# ---- Historia uproszczona (tylko datetime + total_value) ----
@router.get("/{portfolio_id}/history/summary")
def get_portfolio_history_summary(portfolio_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    return service.get_portfolio_summary(portfolio_id)


@router.get("/user/{user_id}/history/summary")
def get_user_portfolio_history_summary(user_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    portfolio = service.get_user_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for user")
    return service.get_portfolio_summary(portfolio.id)


# ---- Stan portfela na dany dzień (po portfolio_id i user_id) ----
@router.get("/{portfolio_id}/state")
def get_portfolio_state_on_date(
    portfolio_id: int,
    date: datetime = Query(..., description="Data w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    service = PortfolioService(db)
    state = service.get_portfolio_state(portfolio_id, date)
    if not state:
        raise HTTPException(status_code=404, detail="No state for given date")
    return state


@router.get("/user/{user_id}/state")
def get_user_portfolio_state_on_date(
    user_id: int,
    date: datetime = Query(..., description="Data w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    service = PortfolioService(db)
    portfolio = service.get_user_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for user")
    state = service.get_portfolio_state(portfolio.id, date)
    if not state:
        raise HTTPException(status_code=404, detail="No state for given date")
    return state

# @router.get("/{user_id}/daily-portfolio/{date}", response_model=UserDetailDTO)
# def get_user_daily_portfolio(user_id: int, date: str):
#     """Get user's portfolio details for a specific date"""
#     user = SimulationService.get_user_daily_portfolio(user_id, date)
#     if not user:
#         raise HTTPException(status_code=404, detail="User portfolio not found for given date")
#     return user
#
# @router.get("/{user_id}/portfolio-history")
# def get_user_portfolio_history(user_id: int):
#     """Get historical portfolio values for a user"""
#     history = SimulationService.get_user_portfolio_history(user_id)
#     if not history:
#         raise HTTPException(status_code=404, detail="User history not found")
#     return history
#
# @router.get("/{user_id}/full-portfolio-history", response_model=List[UserDetail2DTO])
# def get_user_full_portfolio_history(user_id: int):
#     """Get complete historical portfolio details with positions for all dates"""
#     history = SimulationService.get_user_full_portfolio_history(user_id)
#     if not history:
#         raise HTTPException(status_code=404, detail="User portfolio history not found")
#     return history

