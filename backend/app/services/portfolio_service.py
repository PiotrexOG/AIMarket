from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioShare, PortfolioHistory
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate


class PortfolioService:
    def __init__(self, db: Session):
        self.repo = PortfolioRepository(db)

    # ---- Portfele ----
    def create_portfolio(self, data: PortfolioCreate):
        """
        Tworzy nowy portfel dla użytkownika.
        """
        return self.repo.create_portfolio(data)

    def get_portfolio(self, portfolio_id: int):
        """
        Pobiera szczegóły portfela.
        """
        return self.repo.get_portfolio(portfolio_id)

    def get_user_portfolios(self, user_id: int):
        """
        Pobiera wszystkie portfele danego użytkownika.
        """
        return self.repo.get_user_portfolios(user_id)

    def evaluate(self, portfolio_id: int, history_data: PortfolioHistoryCreate) -> PortfolioHistory:
        return self.repo.add_history(portfolio_id, history_data)

    def get_portfolio_state(self, portfolio_id: int, date_time: datetime) -> Optional[dict]:
        """
        Zwraca słownik {cash, shares{ticker: amount}} dla portfela na dany dzień.
        """
        history = self.repo.get_state_at_date(portfolio_id, date_time)
        if not history:
            return None

        return {
            "cash": history.cash,
            "shares": {share.ticker: share.amount for share in history.shares}
        }

    def delete_all(self):
        """
        Usuwa wszystkie portfele, historię i udziały.
        """
        self.repo.delete_all()

    # def get_user_daily_portfolio(cls, user_id: int, date_str: str) -> Optional[UserDetailDTO]:
    #     simulator = cls.users.get(user_id)
    #     if not simulator:
    #         return None
    #
    #     try:
    #         date_time = isoparse(date_str)
    #     except (ValueError, TypeError):
    #         return None
    #
    #     portfolio_details = simulator.calculate_portfolio_details(date_time)
    #     if not portfolio_details:
    #         return None
    #
    #     positions_dto = cls._create_position_details(portfolio_details["positions"])
    #
    #     return UserDetailDTO(
    #         user_id=user_id,
    #         cash=portfolio_details["cash"],
    #         portfolio_value=portfolio_details["total_value"],
    #         positions=positions_dto
    #     )
    #
    # @classmethod
    # def get_user_portfolio_history(cls, user_id: int) -> List[dict]:
    #     simulator = cls.users.get(user_id)
    #     if not simulator:
    #         return []
    #
    #     history_data = []
    #     for entry in simulator.portfolio.history:
    #         date_time = entry['datetime']
    #         portfolio_details = simulator.calculate_portfolio_details(date_time)
    #         if portfolio_details:
    #             history_data.append({
    #                 "timestamp": portfolio_details["date_time"],
    #                 "portfolio_value": portfolio_details["total_value"]
    #             })
    #
    #     return history_data
    #
    # @classmethod
    # def get_user_full_portfolio_history(cls, user_id: int) -> List[UserDetail2DTO]:
    #     """Get complete portfolio history with positions for all dates"""
    #     simulator = cls.users.get(user_id)
    #     if not simulator:
    #         return []
    #
    #     history_data = []
    #     for entry in simulator.portfolio.history:
    #         date_time = entry['datetime']
    #         portfolio_details = simulator.calculate_portfolio_details(date_time)
    #         if portfolio_details:
    #             positions_dto = cls._create_position_details(portfolio_details["positions"])
    #             history_data.append(UserDetail2DTO(
    #                 user_id=user_id,
    #                 date=date_time.isoformat(),  # Dodajemy datę do DTO
    #                 cash=portfolio_details["cash"],
    #                 portfolio_value=portfolio_details["total_value"],
    #                 positions=positions_dto
    #             ))
    #
    #     return history_data
    #
    # @staticmethod
    # def _create_position_details(positions: list[dict]) -> list[PositionDetail]:
    #     return [
    #         PositionDetail(
    #             ticker=pos["ticker"],
    #             shares=pos["shares"],
    #             price=pos["price"],
    #             value=pos["value"]
    #         ) for pos in positions
    #     ]
