from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.dto.portfolio_dto import PortfolioStateDTO, PortfolioSummaryDTO, PositionDetail
from app.db.models.portfolio import PortfolioHistory
from app.repositories.portfolio_repository import PortfolioRepository
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate
from app.services.portfolio_valuation_service import PortfolioValuationService


class PortfolioService:
    def __init__(self, db: Session, portfolio_valuation_service: PortfolioValuationService):
        self.repo = PortfolioRepository(db)
        self.portfolio_valuation_service = portfolio_valuation_service

    # ---- Portfele ----
    def create_portfolio(self, data: PortfolioCreate):
        """Tworzy nowy portfel dla użytkownika."""
        return self.repo.create(data)

    def get_by_user_id(self, user_id: int):
        """Pobiera portfel przypisany do użytkownika."""
        return self.repo.get_by_user(user_id)

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        """Pobiera najnowszy wpis historii dla danego portfela."""
        return self.repo.get_latest_history(portfolio_id)

    def evaluate(self, portfolio_id: int, history_data: PortfolioHistoryCreate) -> PortfolioHistory:
        """Dodaje nowy wpis historii portfela."""
        return self.repo.add_history(portfolio_id, history_data)

    def get_portfolio_history(self, portfolio_id: int) -> List[PortfolioStateDTO]:
        """Pobiera całą historię portfela w formacie DTO."""
        history = self.repo.get_history(portfolio_id)
        return [self._convert_to_state_dto(history_item) for history_item in history]

    def get_portfolio_summary(self, portfolio_id: int) -> List[PortfolioSummaryDTO]:
        """Pobiera uproszczoną historię (tylko data i wartość)."""
        history = self.repo.get_history(portfolio_id)
        return [
            PortfolioSummaryDTO(
                date=history_item.datetime.isoformat(),
                portfolio_value=history_item.total_value
            )
            for history_item in history
        ]

    def get_portfolio_state(self, portfolio_id: int, date: datetime) -> Optional[PortfolioStateDTO]:
        """Pobiera stan portfela na konkretną datę."""
        state = self.repo.get_state_at_date(portfolio_id, date)
        if state:
            return self._convert_to_state_dto(state)
        return None

    def _convert_to_state_dto(self, history_item: PortfolioHistory) -> PortfolioStateDTO:
        """Konwertuje PortfolioHistory na PortfolioStateDTO"""
        shares_dict = {share.ticker: share.amount for share in history_item.shares}

        valuation = self.portfolio_valuation_service.calculate_portfolio_details(
            cash=history_item.cash,
            shares=shares_dict,
            date_time=history_item.datetime
        )

        return PortfolioStateDTO(
            user_id=history_item.portfolio.user_id,
            date=history_item.datetime.isoformat(),
            cash=valuation.cash,
            portfolio_value=valuation.total_value,
            positions=[
                PositionDetail(
                    ticker=position.ticker,
                    shares=position.shares,
                    price=position.price,
                    value=position.value
                ) for position in valuation.positions
            ]
        )

