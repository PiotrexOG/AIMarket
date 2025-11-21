from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session

from app.clients.yahoo_client import YahooClient
from app.config import DEBUG_RESET, USERS, STARTING_CASH
from app.db.schemas.market_data import MarketDataCreate
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate, PortfolioShareCreate
from app.db.schemas.user import UserCreate
from app.services.market_data_service import MarketDataService
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.services.portfolio_transaction_service import PortfolioTransactionService
from app.services.user_service import UserService
from app.services.portfolio_service import PortfolioService
from app.simulation.user_simulator import UserSimulator

class SimulationService:
    def __init__(self, db: Session, tickers: list[str], zero_time: datetime, start_time: datetime, end_time: datetime):
        self.db = db
        self.tickers = tickers
        self.zero_time = zero_time
        self.start_time = start_time
        self.end_time = end_time

        self.market_data_service = MarketDataService(db)
        self.user_service = UserService(db)
        self.valuation_service = PortfolioValuationService(self.market_data_service)
        self.portfolio_service = PortfolioService(db, self.valuation_service)
        self.transaction_service  = PortfolioTransactionService(db, self.portfolio_service)
        self.yahoo_client = YahooClient()
        self.users: Dict[int, UserSimulator] = {}

    # ---- Krok 1: Pobierz dane z Yahoo i zapisz do bazy ----
    def fetch_market_data(self, interval: str):
        """
        Pobiera dane rynkowe dla wszystkich tickerów,
        ale tylko jeśli w bazie jeszcze ich nie ma.
        """
        for ticker in self.tickers:
            # sprawdzenie, czy są już dane dla tego tickera w zakresie dat
            existing = self.market_data_service.has_data_in_range(
                ticker=ticker,
                start=self.zero_time,
                end=self.end_time
            )

            if existing:
                print(f"⏭ Dane dla {ticker} już istnieją w bazie, pomijam pobieranie")
                continue

            df = self.yahoo_client.fetch_history(
                ticker, self.zero_time, self.end_time, interval
            )
            if df.empty:
                print(f"⚠️ Brak danych dla {ticker}")
                continue

            for _, row in df.iterrows():
                self.market_data_service.add_market_data(
                    MarketDataCreate(
                        datetime=row["Datetime"],
                        ticker=row["Ticker"],
                        open=row["Open"],
                        high=row["High"],
                        low=row["Low"],
                        close=row["Close"],
                        volume=row["Volume"],
                    )
                )
            print(f"✅ Dane dla {ticker} zapisane do bazy")

    # ---- Krok 2: Inicjalizacja użytkowników i portfeli ----
    def initialize_users(self):
        existing_users = self.user_service.list_users()
        users_to_init = []
        starting_cash = STARTING_CASH
        user_names = list(USERS.keys())

        if DEBUG_RESET or not existing_users:
            # 🔄 czysta inicjalizacja
            for name in user_names:
                user = self.user_service.create_user(UserCreate(name=name))
                self.portfolio_service.create_portfolio(PortfolioCreate(
                    name=f"Portfolio {name}",
                    user_id=user.id
                ))

                users_to_init.append((user, starting_cash, {}))
        else:
            # 📥 odtwarzanie stanu z bazy
            for user in existing_users:
                portfolio = self.portfolio_service.get_by_user_id(user.id)
                latest_history = self.portfolio_service.get_latest_history(portfolio.id)

                if latest_history:
                    cash = latest_history.cash
                    shares = {s.ticker: s.amount for s in latest_history.shares}
                else:
                    cash = starting_cash
                    shares = {}

                users_to_init.append((user, cash, shares))

        # 🚀 Wspólna logika budowania UserSimulatorów
        for user, cash, shares in users_to_init:
            decision_maker_factory = USERS[user.name]
            decision_maker = decision_maker_factory()

            self.users[user.id] = UserSimulator(
                user_id=user.id,
                starting_cash=cash,
                shares=shares,
                decision_maker=decision_maker,
                portfolio_service=self.portfolio_service,
                market_data_service=self.market_data_service,
                valuation_service=self.valuation_service,
                transaction_service=self.transaction_service
            )

            if DEBUG_RESET or not existing_users or not shares:
                history_data = PortfolioHistoryCreate(
                    datetime=self.start_time,
                    cash=cash,
                    shares=[
                        PortfolioShareCreate(ticker=t, amount=a)
                        for t, a in shares.items()
                    ]
                )
                self.portfolio_service.evaluate(user.id, history_data)

    # ---- Krok 3: Symulacja krok po kroku ----
    def run_simulation(self):
        current_time = self.start_time
        print(current_time)
        while current_time <= self.end_time:
            self._simulate_time_step(current_time)
            current_time += timedelta(weeks=1)
        print("✅ Symulacja zakończona.")

    # ---- Krok 4: Symulacja pojedynczego kroku czasu ----
    def _simulate_time_step(self, current_time: datetime):
        for user_simulator in self.users.values():
            user_simulator.process_day(current_time)
