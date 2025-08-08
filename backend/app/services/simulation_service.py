from datetime import datetime, timedelta
from typing import Dict, Optional
from dateutil.parser import isoparse

from app.core.user_simulator import UserSimulator
from app.core.market_data_store import MarketDataStore
from app.config import TICKERS, start_time, end_time
from app.models.user_models import UserDTO, UserDetailDTO, PositionDetail



class SimulationService:
    users: Dict[int, UserSimulator] = {}
    market_data: MarketDataStore = MarketDataStore(
        tickers=TICKERS,
        start_date=start_time,
        end_date=end_time,
    )

    @classmethod
    def initialize_users(cls, no_users: int, starting_cash: float) -> None:
        for user_id in range(1, no_users + 1):
            cls.users[user_id] = UserSimulator(
                user_id=user_id,
                starting_cash=starting_cash,
                market_data_store=cls.market_data,
                use_model=False
            )

    @classmethod
    def start_simulation(cls) -> None:
        current_time = start_time
        while current_time <= end_time:
            cls._simulate_time_step(current_time)
            current_time += timedelta(hours=1)
        print("✅ Symulacja zakończona.")

    @classmethod
    def _simulate_time_step(cls, current_time: datetime) -> None:
        for user_simulator in cls.users.values():
            user_simulator.process_day(current_time)

    @classmethod
    def get_user(cls, user_id: int, date_time_str: str) -> Optional[UserDetailDTO]:
        simulator = cls.users.get(user_id)
        if not simulator:
            return None

        try:
            date_time = isoparse(date_time_str)
        except (ValueError, TypeError):
            return None

        portfolio_details = simulator.calculate_portfolio_details(date_time)
        if not portfolio_details:
            return None

        positions_dto = cls._create_position_details(portfolio_details["positions"])

        return UserDetailDTO(
            user_id=user_id,
            cash=portfolio_details["cash"],
            portfolio_value=portfolio_details["total_value"],
            positions=positions_dto
        )

    @staticmethod
    def _create_position_details(positions: list[dict]) -> list[PositionDetail]:
        return [
            PositionDetail(
                ticker=pos["ticker"],
                shares=pos["shares"],
                price=pos["price"],
                value=pos["value"]
            ) for pos in positions
        ]
