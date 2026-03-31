from app.db.models.portfolio import Portfolio, PortfolioHistory, PortfolioShare
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---- Portfolio ----
    def create(self, data: PortfolioCreate) -> Portfolio:
        """Tworzy nowy portfel dla użytkownika."""
        if isinstance(data, dict):
            db_obj = Portfolio(**data)
        else:
            db_obj = Portfolio(**data.dict())

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        """Pobiera najnowszy wpis historii dla danego portfela."""
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(PortfolioHistory.portfolio_id == portfolio_id)
            .order_by(PortfolioHistory.datetime.desc(), PortfolioHistory.id.desc())
            .first()
        )

    def get_by_user(self, user_id: int) -> Portfolio:
        """Pobiera wszystkie portfele danego użytkownika."""
        return (
            self.db.query(Portfolio)
            .filter(Portfolio.user_id == user_id)
            .first()
        )

    # ---- Historia portfela ----
    def get_history(self, portfolio_id: int) -> List[PortfolioHistory]:
        """Pobiera całą historię portfela (łącznie z udziałami)."""
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(PortfolioHistory.portfolio_id == portfolio_id)
            .order_by(PortfolioHistory.datetime.asc())
            .all()
        )

    def get_state_at_date(
        self, portfolio_id: int, date_time: datetime
    ) -> Optional[PortfolioHistory]:
        """
        Pobiera najnowszy stan portfela (PortfolioHistory) na dany dzień.
        Ładujemy od razu powiązane udziały (PortfolioShare).
        """
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(
                PortfolioHistory.portfolio_id == portfolio_id,
                PortfolioHistory.datetime <= date_time,
            )
            .order_by(PortfolioHistory.datetime.desc(), PortfolioHistory.id.desc())
            .first()
        )

    # ---- Portfolio History ----
    def add_history(
        self, portfolio_id: int, history_data: PortfolioHistoryCreate
    ) -> PortfolioHistory:
        """Dodaje nowy wpis do historii portfela wraz z udziałami."""
        history_obj = PortfolioHistory(
            portfolio_id=portfolio_id,
            datetime=history_data.datetime,
            cash=history_data.cash
        )
        self.db.add(history_obj)
        self.db.flush()  # żeby mieć ID przed dodaniem shares

        for share in history_data.shares:
            share_obj = PortfolioShare(
                portfolio_history_id=history_obj.id,
                ticker=share.ticker,
                amount=share.amount,
            )
            self.db.add(share_obj)

        self.db.commit()
        self.db.refresh(history_obj)
        return history_obj

