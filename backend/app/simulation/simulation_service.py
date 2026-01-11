from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session

from app.clients.yahoo_client import YahooClient
from app.config import DEBUG_RESET, USERS, STARTING_CASH
from app.db.schemas.layers.market_data_scheme import MarketDataCreate
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate, PortfolioShareCreate
from app.db.schemas.user import UserCreate
from app.services.layers.analyst_grades_service import AnalystGradesService
from app.services.layers.company_news_service import CompanyNewsService
from app.services.layers.fundamental_snapshot_service import FundamentalSnapshotService
from app.services.layers.market_data_service import MarketDataService
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.services.portfolio_transaction_service import PortfolioTransactionService
from app.services.user_service import UserService
from app.services.portfolio_service import PortfolioService
from app.simulation.user_simulator import UserSimulator
from app.testy.compute import data_fundamentals, quarter_helper
from app.testy.scrap.analyst_grades import fetch_analyst_grades
from app.testy.scrap.company_news import fetch_all_company_news


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
        self.fundamental_snapshot_service = FundamentalSnapshotService(db)
        self.analyst_grades_service = AnalystGradesService(db)
        self.company_news_service = CompanyNewsService(db)
        self.yahoo_client = YahooClient()
        self.users: Dict[int, UserSimulator] = {}


    # Rozszerzona wersja Twojej metody
    def fetch_data_fundaments(self):

        quarters = quarter_helper.get_required_quarters(self.start_time, self.end_time)

        for ticker in self.tickers:
            for year, quarter in quarters:
                funds = data_fundamentals.calculate(
                    symbol=ticker,
                    current_year=year,
                    current_quarter=quarter,
                )

                raw = funds.copy()
                as_of_date = datetime.fromisoformat(raw.pop("date"))

                self.fundamental_snapshot_service.save(
                    ticker=ticker,
                    date_time=as_of_date,
                    data=raw,
                )
            print(f"✅ Fundaments dla {ticker} zapisana")

    # Rozszerzona wersja Twojej metody
    def fetch_company_news(self):

        for ticker in self.tickers:
            news = fetch_all_company_news(
                symbol=ticker,
                from_date=self.start_time,
                to_date=self.end_time,
            )

            for g in news:
                as_of_date = datetime.fromisoformat(g["datetime"])

                payload = {
                    "headline": g.get("headline"),
                    "summary": g.get("summary")
                }

                self.company_news_service.save(
                    ticker=ticker,
                    date_time=as_of_date,
                    data=payload,
                )
            print(f"✅ Company news dla {ticker} zapisana")

    # Rozszerzona wersja Twojej metody
    def fetch_analyst_grades(self):

        for ticker in self.tickers:
            grades = fetch_analyst_grades(
                symbol=ticker,
                start_date=self.start_time,
                end_date=self.end_time,
            )

            for g in grades:
                as_of_date = datetime.fromisoformat(g["date"])

                payload = {
                    "analystRatingsStrongBuy": g.get("analystRatingsStrongBuy"),
                    "analystRatingsBuy": g.get("analystRatingsBuy"),
                    "analystRatingsHold": g.get("analystRatingsHold"),
                    "analystRatingsSell": g.get("analystRatingsSell"),
                    "analystRatingsStrongSell": g.get("analystRatingsStrongSell"),
                }

                self.analyst_grades_service.save(
                    ticker=ticker,
                    date_time=as_of_date,
                    data=payload,
                )
            print(f"✅ Analyst grades dla {ticker} zapisana")

    # Rozszerzona wersja Twojej metody
    def fetch_market_data(self, interval: str):
        """
        Pobiera historię cen oraz dane kontekstowe.
        """
        # Pobieranie OHLCV (to co już masz)
        for ticker in self.tickers:
            existing = self.market_data_service.has_data_in_range(
                ticker=ticker, start=self.zero_time, end=self.end_time
            )

            if not existing:
                df = self.yahoo_client.fetch_history(ticker, self.zero_time, self.end_time, interval)
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
                print(f"✅ Historia OHLCV dla {ticker} zapisana")


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
                transaction_service=self.transaction_service,
                fundamental_service=self.fundamental_snapshot_service
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
