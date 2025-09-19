from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload
from app.db.models.portfolio import Portfolio, PortfolioHistory, PortfolioShare
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate

class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---- Portfolio ----
    def create_portfolio(self, data: PortfolioCreate) -> Portfolio:
        if isinstance(data, dict):
            db_obj = Portfolio(**data)
        else:
            db_obj = Portfolio(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_portfolio(self, portfolio_id: int):
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def get_user_portfolios(self, user_id: int):
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    # ---- Historia portfela ----
    def get_portfolio_history(self, portfolio_id: int) -> List[PortfolioHistory]:
        """ Pobiera całą historię portfela (łącznie z udziałami). """
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(PortfolioHistory.portfolio_id == portfolio_id)
            .order_by(PortfolioHistory.datetime.asc())
            .all()
        )

    def get_state_at_date(self, portfolio_id: int, date_time: datetime) -> Optional[PortfolioHistory]:
        """
        Pobiera najnowszy stan portfela (PortfolioHistory) na dany dzień.
        Ładujemy od razu powiązane udziały (PortfolioShare).
        """
        return (
            self.db.query(PortfolioHistory)
            .options(joinedload(PortfolioHistory.shares))
            .filter(
                PortfolioHistory.portfolio_id == portfolio_id,
                PortfolioHistory.datetime <= date_time
            )
            .order_by(PortfolioHistory.datetime.desc())
            .first()
        )

    # ---- Portfolio History ----
    def add_history(self, portfolio_id: int, history_data: PortfolioHistoryCreate) -> PortfolioHistory:
        history_obj = PortfolioHistory(
            portfolio_id=portfolio_id,
            datetime=history_data.datetime,
            cash=history_data.cash,
            total_value=history_data.total_value  # <--- prosto z DTO
        )
        self.db.add(history_obj)
        self.db.flush()

        for share in history_data.shares:
            share_obj = PortfolioShare(
                portfolio_history_id=history_obj.id,
                ticker=share.ticker,
                amount=share.amount
            )
            self.db.add(share_obj)

        self.db.commit()

        self.db.refresh(history_obj)
        return history_obj
