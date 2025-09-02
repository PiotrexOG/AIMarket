from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioHistoryCreate
from app.services.portfolio_service import PortfolioService
from app.database import get_db

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

@router.get("/{portfolio_id}", response_model=PortfolioRead)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    portfolio = service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.get("/user/{user_id}", response_model=List[PortfolioRead])
def get_user_portfolios(user_id: int, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    return service.get_user_portfolios(user_id)

@router.get("/{user_id}/daily-portfolio/{date}", response_model=UserDetailDTO)
def get_user_daily_portfolio(user_id: int, date: str):
    """Get user's portfolio details for a specific date"""
    user = SimulationService.get_user_daily_portfolio(user_id, date)
    if not user:
        raise HTTPException(status_code=404, detail="User portfolio not found for given date")
    return user

@router.get("/{user_id}/portfolio-history")
def get_user_portfolio_history(user_id: int):
    """Get historical portfolio values for a user"""
    history = SimulationService.get_user_portfolio_history(user_id)
    if not history:
        raise HTTPException(status_code=404, detail="User history not found")
    return history

@router.get("/{user_id}/full-portfolio-history", response_model=List[UserDetail2DTO])
def get_user_full_portfolio_history(user_id: int):
    """Get complete historical portfolio details with positions for all dates"""
    history = SimulationService.get_user_full_portfolio_history(user_id)
    if not history:
        raise HTTPException(status_code=404, detail="User portfolio history not found")
    return history

