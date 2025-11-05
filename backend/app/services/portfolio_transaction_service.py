from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.db.schemas.portfolio import PortfolioTransactionRead
from app.repositories.portfolio_transaction_repository import PortfolioTransactionRepository


class PortfolioTransactionService:
    def __init__(self, db: Session):
        self.repo = PortfolioTransactionRepository(db)

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
