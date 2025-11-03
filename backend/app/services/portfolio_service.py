from datetime import datetime, timedelta
from typing import List, Optional, Literal
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.dto.portfolio_dto import PortfolioStateDTO, PortfolioSummaryDTO, PositionDetail
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.db.schemas.portfolio import PortfolioCreate
from app.db.models.portfolio import PortfolioHistory
from app.shared.types import ValuationInterval, INTERVAL_MAP


# ---- Funkcje pomocnicze poza klasą ----
def _create_valuation_dto(valuation, user_id: int = None, detailed: bool = False):
    """Tworzy DTO na podstawie wyceny i flagi detailed."""
    if detailed:
        return PortfolioStateDTO(
            user_id=user_id,
            date=valuation.date.isoformat(),
            cash=valuation.cash,
            portfolio_value=valuation.portfolio_value,
            positions=[
                PositionDetail(
                    ticker=p.ticker,
                    shares=p.shares,
                    price=p.price,
                    value=p.value
                ) for p in valuation.positions
            ],
        )
    else:
        return PortfolioSummaryDTO(
            date=valuation.date.isoformat(),
            portfolio_value=valuation.portfolio_value,
        )


class PortfolioService:
    def __init__(self, db: Session, portfolio_valuation_service: PortfolioValuationService):
        self.repo = PortfolioRepository(db)
        self.portfolio_valuation_service = portfolio_valuation_service

    # ---- Podstawowe operacje ----
    def create_portfolio(self, data: PortfolioCreate):
        return self.repo.create(data)

    def get_by_user_id(self, user_id: int):
        return self.repo.get_by_user(user_id)

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        return self.repo.get_latest_history(portfolio_id)

    def evaluate(self, portfolio_id: int, history_data):
        return self.repo.add_history(portfolio_id, history_data)

    def _create_dto_from_history_entry(self, history_entry, date: datetime, detailed: bool = True):
        """Tworzy DTO na podstawie pojedynczego wpisu historii portfela."""
        shares_dict = {share.ticker: share.amount for share in history_entry.shares}
        valuation = self.portfolio_valuation_service.calculate_portfolio_details(
            cash=history_entry.cash,
            shares=shares_dict,
            date_time=date,
        )
        return _create_valuation_dto(
            valuation=valuation,
            user_id=history_entry.portfolio.user_id,
            detailed=detailed
        )

    def get_portfolio_history(self, portfolio_id: int, detailed: bool = True):
        """Zwraca historię portfela zapisaną w bazie (PortfolioHistory)."""
        history = self.repo.get_history(portfolio_id)
        if not history:
            return []

        return [
            self._create_dto_from_history_entry(h, h.datetime, detailed)
            for h in history
        ]

    def compute_portfolio_state_at_date(
            self,
            portfolio_id: int,
            date: datetime,
            detailed: bool
    ):
        """Pobiera stan portfela z repo i wylicza jego bieżącą wartość rynkową."""
        state = self.repo.get_state_at_date(portfolio_id, date)
        if not state:
            return None

        return self._create_dto_from_history_entry(state, date, detailed)

    # ---- Wycena (valuation) w przedziale czasu ----
    def get_portfolio_valuation_in_range(
            self,
            portfolio_id: int,
            start: datetime,
            end: datetime,
            interval: ValuationInterval,
            detailed: bool = False,
    ) -> dict:
        """Zwraca wycenę portfela w zadanym zakresie, z aktualnym stanem dla każdej chwili."""
        step = INTERVAL_MAP.get(interval)
        if not step:
            raise ValueError(f"Unsupported interval: {interval}")

        valuations = []
        current = start

        while current <= end:
            dto = self.compute_portfolio_state_at_date(
                portfolio_id=portfolio_id,
                date=current,
                detailed=detailed
            )
            if dto:
                valuations.append(dto)

            current += step

        if not valuations:
            raise HTTPException(status_code=404, detail="No valuation data in range")

        # Oblicz zmiany procentowe
        start_value = valuations[0].portfolio_value if hasattr(valuations[0], 'portfolio_value') else valuations[0][
            'portfolio_value']
        end_value = valuations[-1].portfolio_value if hasattr(valuations[-1], 'portfolio_value') else valuations[-1][
            'portfolio_value']
        absolute_change = end_value - start_value
        percent_change = (absolute_change / start_value * 100) if start_value != 0 else 0.0

        return {
            "percent_change": round(percent_change, 2),
            "history": valuations
        }
