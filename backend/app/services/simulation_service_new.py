from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session

from app.clients.yahoo_client import YahooClient
from app.schemas.market_data import MarketDataCreate
from app.schemas.portfolio import PortfolioCreate
from app.schemas.user import UserCreate
from app.services.market_data_service import MarketDataService
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.services.user_service import UserService
from app.services.portfolio_service import PortfolioService
from app.models.portfolio import PortfolioShare
from app.simulation.user_simulator import UserSimulator

class SimulationService:
    def __init__(self, db: Session, tickers: list[str], start_time: datetime, end_time: datetime):
        self.db = db
        self.tickers = tickers
        self.start_time = start_time
        self.end_time = end_time

        self.market_data_service = MarketDataService(db)
        self.user_service = UserService(db)
        self.valuation_service = PortfolioValuationService(self.market_data_service)
        self.portfolio_service = PortfolioService(db, self.valuation_service)
        self.yahoo_client = YahooClient()
        self.users: Dict[int, UserSimulator] = {}

    # ---- Krok 1: Pobierz dane z Yahoo i zapisz do bazy ----
    def fetch_market_data(self, interval: str = "1h"):

        for ticker in self.tickers:
            df = self.yahoo_client.fetch_history(ticker, self.start_time, self.end_time, interval)
            if df.empty:
                print(f"⚠️ Brak danych dla {ticker}")
                continue

            for _, row in df.iterrows():
                self.market_data_service.add_market_data(
                    MarketDataCreate(
                        datetime = row["Datetime"],
                        ticker = row["Ticker"],
                        open = row["Open"],
                        high = row["High"],
                        low = row["Low"],
                        close = row["Close"],
                        volume = row["Volume"]
                    )
                )
            print(f"✅ Dane dla {ticker} zapisane do bazy")

    # ---- Krok 2: Inicjalizacja użytkowników i portfeli ----
    def initialize_users(self, no_users: int, starting_cash: float):
        for user_id in range(1, no_users + 1):
            # Tworzymy użytkownika w bazie
            user = self.user_service.create_user(UserCreate(name = f"User {user_id}"))

            # Tworzymy portfel w bazie
            self.portfolio_service.create_portfolio(PortfolioCreate(
                name=f"Portfolio {user_id}",
                user_id=user.id
            ))

            # Tworzymy symulator użytkownika
            self.users[user.id] = UserSimulator(
                user_id=user.id,
                starting_cash=starting_cash,
                portfolio_service=self.portfolio_service,
                market_data_service=self.market_data_service,
                valuation_service=self.valuation_service,
                use_model=False
            )

    # ---- Krok 3: Symulacja krok po kroku ----
    def run_simulation(self):
        current_time = self.start_time
        print(current_time)
        while current_time <= self.end_time:
            self._simulate_time_step(current_time)
            current_time += timedelta(hours=1)
        print("✅ Symulacja zakończona.")

    # ---- Krok 4: Symulacja pojedynczego kroku czasu ----
    def _simulate_time_step(self, current_time: datetime):
        for user_simulator in self.users.values():
            user_simulator.process_day(current_time)
