from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.schemas.portfolio import PortfolioTransactionRead, PortfolioTickerTransactionRead
from app.dto.portfolio_dto import PortfolioPerformanceSummaryDTO
from app.services.layers.analytical_service import AnalyticalService
from app.services.layers.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.db.database import get_db
from datetime import datetime

from app.services.portfolio_transaction_service import PortfolioTransactionService
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.shared.types import ValuationInterval

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


def get_service(db: Session):
    return PortfolioService(db, PortfolioValuationService(MarketDataService(db)))

def get_transaction_service(db: Session) -> PortfolioTransactionService:
    market_data_service = MarketDataService(db)
    valuation_service = PortfolioValuationService(market_data_service)
    portfolio_service = PortfolioService(db, valuation_service)
    return PortfolioTransactionService(db, portfolio_service)

def get_analytical_service() -> AnalyticalService:
    return AnalyticalService()

# ---- 1️⃣ Historia z bazy ----
@router.get("/{portfolio_id}/history")
def get_portfolio_history(
    portfolio_id: int,
    detailed: bool = Query(True, description="Czy zwrócić szczegółową historię?"),
    db: Session = Depends(get_db)
):
    service = get_service(db)
    history = service.get_portfolio_history(portfolio_id, detailed)

    return history


# ---- 2️⃣ Symulowana wycena (valuation) ----
@router.get("/{portfolio_id}/valuation")
def get_portfolio_valuation(
    portfolio_id: int,
    start: datetime = Query(..., description="Początek zakresu dat"),
    end: datetime = Query(..., description="Koniec zakresu dat"),
    interval: ValuationInterval = Query("1h", description="Interwał czasowy"),
    detailed: bool = Query(False, description="Czy zwrócić szczegółową historię?"),
    db: Session = Depends(get_db)
):
    service = get_service(db)
    return service.get_portfolio_valuation_in_range(portfolio_id, start, end, interval, detailed)

@router.get("/performance-summary", response_model=List[PortfolioPerformanceSummaryDTO])
def get_all_portfolios_performance(
    start: datetime = Query(..., description="Początek okresu do analizy"),
    end: datetime = Query(..., description="Koniec okresu do analizy"),
    db: Session = Depends(get_db)
):

    service = get_service(db)
    return service.get_all_portfolios_performance_summary(start, end)

@router.get("/{portfolio_id}/performance-summary", response_model=PortfolioPerformanceSummaryDTO)
def get_portfolio_performance_summary(
    portfolio_id: int,
    start: datetime = Query(..., description="Początek okresu do analizy"),
    end: datetime = Query(..., description="Koniec okresu do analizy"),
    db: Session = Depends(get_db)
):

    service = get_service(db)
    return service.get_portfolio_performance_summary(portfolio_id, start, end)

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

    return state

@router.get("/{portfolio_id}/transactions", response_model=list[PortfolioTransactionRead])
def get_portfolio_transactions(portfolio_id: int, db: Session = Depends(get_db)):
    """Zwraca listę wszystkich transakcji dla danego portfela."""
    tx_service = get_transaction_service(db)
    transactions = tx_service.get_transactions(portfolio_id)

    return transactions

@router.get("/{portfolio_id}/transactions/{ticker}", response_model=list[PortfolioTickerTransactionRead])
def get_portfolio_ticker_transactions(
    portfolio_id: int,
    ticker: str,
    start: Optional[datetime] = Query(None, description="Początek zakresu dat"),
    end: Optional[datetime] = Query(None, description="Koniec zakresu dat"),
    db: Session = Depends(get_db),
):
    """Zwraca transakcje dla danego portfela i konkretnego tickera (z ratio historycznym), opcjonalnie w zakresie dat."""
    tx_service = get_transaction_service(db)
    return tx_service.get_ticker_transactions(
        portfolio_id=portfolio_id,
        ticker=ticker,
        start=start,
        end=end
    )
