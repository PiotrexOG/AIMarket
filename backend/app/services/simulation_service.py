# from datetime import datetime, timedelta
# from typing import Dict, Optional, List
# from dateutil.parser import isoparse
#
# from app.core.user_simulator import UserSimulator
# from app.core.market_data_store import MarketDataStore
# from app.config import TICKERS, START_TIME, END_TIME
# from app.models.user_models import UserDTO, UserDetailDTO, PositionDetail, UserDetail2DTO
#
#
# class SimulationService:
#     users: Dict[int, UserSimulator] = {}
#     market_data: MarketDataStore = MarketDataStore(
#         tickers=TICKERS,
#         start_date=START_TIME,
#         end_date=END_TIME,
#     )
#
#     @classmethod
#     def initialize_users(cls, no_users: int, starting_cash: float) -> None:
#         for user_id in range(1, no_users + 1):
#             cls.users[user_id] = UserSimulator(
#                 user_id=user_id,
#                 starting_cash=starting_cash,
#                 market_data_store=cls.market_data,
#                 use_model=False
#             )
#
#     @classmethod
#     def start_simulation(cls) -> None:
#         current_time = START_TIME
#         while current_time <= END_TIME:
#             cls._simulate_time_step(current_time)
#             current_time += timedelta(hours=1)
#         print("✅ Symulacja zakończona.")
#
#     @classmethod
#     def _simulate_time_step(cls, current_time: datetime) -> None:
#         for user_simulator in cls.users.values():
#             user_simulator.process_day(current_time)
#
#     @classmethod
#     def get_user_daily_portfolio(cls, user_id: int, date_str: str) -> Optional[UserDetailDTO]:
#         simulator = cls.users.get(user_id)
#         if not simulator:
#             return None
#
#         try:
#             date_time = isoparse(date_str)
#         except (ValueError, TypeError):
#             return None
#
#         portfolio_details = simulator.calculate_portfolio_details(date_time)
#         if not portfolio_details:
#             return None
#
#         positions_dto = cls._create_position_details(portfolio_details["positions"])
#
#         return UserDetailDTO(
#             user_id=user_id,
#             cash=portfolio_details["cash"],
#             portfolio_value=portfolio_details["total_value"],
#             positions=positions_dto
#         )
#
#     @classmethod
#     def get_user_portfolio_history(cls, user_id: int) -> List[dict]:
#         simulator = cls.users.get(user_id)
#         if not simulator:
#             return []
#
#         history_data = []
#         for entry in simulator.portfolio.history:
#             date_time = entry['datetime']
#             portfolio_details = simulator.calculate_portfolio_details(date_time)
#             if portfolio_details:
#                 history_data.append({
#                     "timestamp": portfolio_details["date_time"],
#                     "portfolio_value": portfolio_details["total_value"]
#                 })
#
#         return history_data
#
#     @classmethod
#     def get_user_full_portfolio_history(cls, user_id: int) -> List[UserDetail2DTO]:
#         """Get complete portfolio history with positions for all dates"""
#         simulator = cls.users.get(user_id)
#         if not simulator:
#             return []
#
#         history_data = []
#         for entry in simulator.portfolio.history:
#             date_time = entry['datetime']
#             portfolio_details = simulator.calculate_portfolio_details(date_time)
#             if portfolio_details:
#                 positions_dto = cls._create_position_details(portfolio_details["positions"])
#                 history_data.append(UserDetail2DTO(
#                     user_id=user_id,
#                     date=date_time.isoformat(),  # Dodajemy datę do DTO
#                     cash=portfolio_details["cash"],
#                     portfolio_value=portfolio_details["total_value"],
#                     positions=positions_dto
#                 ))
#
#         return history_data
#
#     @staticmethod
#     def _create_position_details(positions: list[dict]) -> list[PositionDetail]:
#         return [
#             PositionDetail(
#                 ticker=pos["ticker"],
#                 shares=pos["shares"],
#                 price=pos["price"],
#                 value=pos["value"]
#             ) for pos in positions
#         ]
