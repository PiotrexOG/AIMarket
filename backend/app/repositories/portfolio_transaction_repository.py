from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from app.db.models.portfolio import PortfolioTransaction


class PortfolioTransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_transaction(self, **kwargs) -> PortfolioTransaction:
        total_value = round(kwargs['quantity'] * kwargs['price'], 2)
        tx = PortfolioTransaction(
            portfolio_id=kwargs['portfolio_id'],
            datetime=kwargs['datetime_'],
            ticker=kwargs['ticker'],
            type=kwargs['type_'],
            quantity=kwargs['quantity'],
            price=round(kwargs['price'], 2),
            total_value=total_value,
        )
        self.db.add(tx)
        return tx

    def get_by_portfolio_and_ticker(
            self,
            portfolio_id: int,
            ticker: str,
            start: datetime = None,
            end: datetime = None
    ) -> Sequence[PortfolioTransaction]:
        """Zwraca wszystkie transakcje dla danego portfela i tickera, opcjonalnie w zakresie dat."""
        query = self.db.query(PortfolioTransaction).filter(
            PortfolioTransaction.portfolio_id == portfolio_id,
            PortfolioTransaction.ticker == ticker,
        )

        if start:
            query = query.filter(PortfolioTransaction.datetime >= start)
        if end:
            query = query.filter(PortfolioTransaction.datetime <= end)

        return query.order_by(PortfolioTransaction.datetime.asc()).all()

    def get_by_portfolio(self, portfolio_id: int) -> Sequence[PortfolioTransaction]:
        """Zwraca wszystkie transakcje dla danego portfela."""
        return (
            self.db.query(PortfolioTransaction)
            .filter(PortfolioTransaction.portfolio_id == portfolio_id)
            .order_by(PortfolioTransaction.datetime.asc())
            .all()
        )

