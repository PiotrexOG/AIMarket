from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioHistoryCreate
from app.services.portfolio_service import PortfolioService
from app.database import get_db

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

@router.post("/", response_model=PortfolioRead)
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    return service.create_portfolio(data)

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

@router.post("/{portfolio_id}/history", response_model=PortfolioRead)
def add_portfolio_history(portfolio_id: int, history_data: PortfolioHistoryCreate, db: Session = Depends(get_db)):
    service = PortfolioService(db)
    service.add_portfolio_history(portfolio_id, history_data)
    return service.get_portfolio(portfolio_id)
