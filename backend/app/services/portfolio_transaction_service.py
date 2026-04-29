from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.schemas.portfolio import PortfolioTransactionRead, PortfolioTickerTransactionRead
from app.repositories.portfolio_transaction_repository import PortfolioTransactionRepository
from app.services.portfolio_service import PortfolioService


class PortfolioTransactionService:
    def __init__(self, db: Session, portfolio_service: PortfolioService):
        self.repo = PortfolioTransactionRepository(db)
        self.portfolio_service = portfolio_service

    def record_transaction(
        self,
        portfolio_id: int,
        ticker: str,
        type_: str,
        quantity: int,
        price: float,
        datetime_: datetime,
    ) -> PortfolioTransactionRead:
        """Zapisuje transakcję w bazie i zwraca w formacie DTO."""
        tx = self.repo.add_transaction(
            portfolio_id=portfolio_id,
            ticker=ticker,
            type_=type_,
            quantity=quantity,
            price=price,
            datetime_=datetime_,
        )
        self.repo.db.commit()
        self.repo.db.refresh(tx)

        return PortfolioTransactionRead.model_validate(tx, from_attributes=True)

    def get_transactions(self, portfolio_id: int) -> List[PortfolioTransactionRead]:
        """Zwraca listę wszystkich transakcji dla portfela jako DTO."""
        txs = self.repo.get_by_portfolio(portfolio_id)
        return [
            PortfolioTransactionRead.model_validate(tx, from_attributes=True)
            for tx in txs
        ]

    def get_ticker_transactions(
            self,
            portfolio_id: int,
            ticker: str,
            start: datetime = None,
            end: datetime = None
    ) -> List["PortfolioTickerTransactionRead"]:
        """Zwraca transakcje dla danego tickera z ratio historycznym, opcjonalnie w zakresie dat."""
        txs = self.repo.get_by_portfolio_and_ticker(
            portfolio_id=portfolio_id,
            ticker=ticker,
            start=start,
            end=end
        )

        result = []
        for tx in txs:
            portfolio_state = self.portfolio_service.compute_portfolio_state_at_date(
                portfolio_id=portfolio_id,
                date=tx.datetime,
                detailed=False
            )
            if not portfolio_state or portfolio_state.portfolio_value == 0:
                continue

            sign = 1 if tx.type == "BUY" else -1
            total_value = tx.quantity * tx.price
            ratio = round(sign * (total_value / portfolio_state.portfolio_value), 4)

            result.append(
                PortfolioTickerTransactionRead(
                    datetime=tx.datetime,
                    quantity=sign * tx.quantity,
                    ratio=ratio,
                    price=tx.price,
                    total_value=tx.total_value
                )
            )

        return result