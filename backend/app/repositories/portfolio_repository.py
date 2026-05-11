from app.db.models.portfolio import Portfolio, PortfolioHistory, PortfolioShare, PortfolioMetricWeight
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---- Portfolio ----
    def create(self, data: PortfolioCreate) -> Portfolio:
        """Tworzy nowy portfel wraz z jego wagami metryk."""
        # 1. Konwersja danych na słownik i wyciągnięcie metryk
        data_dict = data.model_dump() if hasattr(data, "model_dump") else data.dict()
        metric_weights_dict = data_dict.pop("metric_weights", {})

        # 2. Tworzenie głównego obiektu Portfolio
        db_portfolio = Portfolio(**data_dict)
        self.db.add(db_portfolio)
        self.db.flush()  # Pobieramy ID portfela przed commitem

        # 3. Tworzenie wpisów wag metryk
        for m_name, m_weight in metric_weights_dict.items():
            mw_obj = PortfolioMetricWeight(
                portfolio_id=db_portfolio.id,
                metric_name=m_name,
                weight=m_weight
            )
            self.db.add(mw_obj)

        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    def get_by_id(self, portfolio_id: int) -> Portfolio:
        return self.db.query(Portfolio).get(portfolio_id)

    def get_all(self) -> List[Portfolio]:
        """Pobiera wszystkie portfele wraz z ich wagami metryk."""
        return (
            self.db.query(Portfolio)
            .options(joinedload(Portfolio.metric_weights))
            .all()
        )

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
        """Pobiera portfel wraz z wagami metryk (dzięki lazy='joined')."""
        return (
            self.db.query(Portfolio)
            .options(joinedload(Portfolio.metric_weights))  # Jawne upewnienie się o załadowaniu wag
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
            cash=round(history_data.cash,2)
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

