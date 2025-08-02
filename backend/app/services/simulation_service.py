from app.core.user_simulator import UserSimulator
from app.core.market_data_store import MarketDataStore
from app.config import TICKERS
from app.models.user_models import UserDTO, UserDetailDTO, PositionDetail
from typing import Dict
from datetime import datetime

# Stan aplikacji
class SimulationService:
    users: Dict[str, UserSimulator] = {}
    market_data: MarketDataStore = MarketDataStore(
        tickers=TICKERS.keys(),
        start_date="2023-10-01",
        end_date="2023-12-31"
    )

    @classmethod
    def initialize_users(cls):
        user_ids = ["user1", "user2"]
        for user_id in user_ids:
            cls.users[user_id] = UserSimulator(
                user_id=user_id,
                starting_cash=10000.0,
                tickers=TICKERS,
                market_data_store=cls.market_data,
                use_model=False
            )

    @classmethod
    def get_user(cls, user_id: str, date_time_str: str) -> UserDetailDTO | None:
        simulator = cls.users.get(user_id)
        if not simulator:
            return None

        date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        portfolio_details = simulator.calculate_portfolio_details(date_time)

        if not portfolio_details:
            return None

        positions_dto = [
            PositionDetail(
                ticker=p["ticker"],
                shares=p["shares"],
                price=p["price"],
                value=p["value"]
            ) for p in portfolio_details["positions"]
        ]

        return UserDetailDTO(
            user_id=user_id,
            cash=portfolio_details["cash"],
            portfolio_value=portfolio_details["total_value"],
            positions=positions_dto
        )

