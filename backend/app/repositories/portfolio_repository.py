from sqlalchemy.orm import Session
from app.models.portfolio import Portfolio, PortfolioHistory, PortfolioShare
from app.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate

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

    # ---- Portfolio History ----
    def add_history(self, portfolio_id: int, history_data: PortfolioHistoryCreate) -> PortfolioHistory:
        history_obj = PortfolioHistory(
            portfolio_id=portfolio_id,
            datetime=history_data.datetime,
            cash=history_data.cash
        )
        self.db.add(history_obj)
        self.db.flush()  # aby mieć id przed dodaniem shares

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
