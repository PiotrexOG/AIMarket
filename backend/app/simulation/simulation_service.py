import json
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from typing import Dict

from sqlalchemy.orm import Session

from app.clients.yahoo_client import YahooClient
from app.config import DEBUG_RESET, USERS, STARTING_CASH
from app.db.schemas.layers.market_data_scheme import MarketDataCreate
from app.db.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate, PortfolioShareCreate
from app.db.schemas.user import UserCreate
from app.models.proccess import process_news_range
from app.services.layers.analyst_grades_service import AnalystGradesService
from app.services.layers.company_daily_summary import CompanyDailySummaryService
from app.services.layers.fundamental_snapshot_service import FundamentalSnapshotService
from app.services.layers.market_data_service import MarketDataService
from app.services.portfolio_valuation_service import PortfolioValuationService
from app.services.portfolio_transaction_service import PortfolioTransactionService
from app.services.user_service import UserService
from app.services.portfolio_service import PortfolioService
from app.simulation.user_simulator import UserSimulator
from app.testy.compute import data_fundamentals
from app.testy.compute.news_score import NewsImportanceScorer, process_importance_range
from app.testy.scrap.analyst_grades import fetch_analyst_grades
from app.testy.scrap.company_news import fetch_all_company_news, save_company_news_incremental, get_latest_datetime
import app.testy.scrap.quarterly as quarterly
import app.testy.scrap.financial as financial
import app.testy.scrap.earning_dates as earning_dates


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
        self.company_daily_summary_service = CompanyDailySummaryService(db)
        self.yahoo_client = YahooClient()
        self.users: Dict[int, UserSimulator] = {}


    # Rozszerzona wersja Twojej metody
    def fetch_data_fundaments(self):


        for ticker in self.tickers:
            earning_dates.save_earnings_by_date(ticker, self.start_time, self.end_time) #comment
            quarters = earning_dates.get_years_and_quarters_from_json(ticker)

            first_year, first_q = quarters[0]
            last_year, last_q = quarters[-1]

            financial.create(ticker, last_year, last_q)#

            quarterly.create(ticker, first_year, f"Q{first_q}", last_year, f"Q{last_q}")

            for year, quarter in quarters:
                funds = data_fundamentals.calculate(
                    symbol=ticker,
                    current_year=year,
                    current_quarter=quarter,
                )

                raw = funds.copy()

                date_value = raw.pop("date")
                if isinstance(date_value, str):
                    as_of_date = datetime.fromisoformat(date_value)
                else:
                    as_of_date = date_value

                self.fundamental_snapshot_service.save(
                    ticker=ticker,
                    date_time=as_of_date,
                    data=raw,
                )
            print(f"✅ Fundaments dla {ticker} zapisana")

    # Rozszerzona wersja Twojej metody
    def fetch_company_news(self):

        for ticker in self.tickers:

            base_path = Path("data") / "company_news"
            last_dt = get_latest_datetime(base_path, ticker, "*.json", "datetime", False)

            if last_dt:
                from_date = last_dt
            else:
                from_date = self.start_time

            news = fetch_all_company_news(
                symbol=ticker,
                from_date=from_date,
                to_date=self.end_time,
            )

            save_company_news_incremental(ticker, news)

            print(f"✅ Company news dla {ticker} zapisane")

    def fetch_company_news_summarize(self):

        for ticker in self.tickers:

            base_path = Path("data") / "company_news_summarized"
            next_dt = get_latest_datetime(base_path, ticker, "summarized_*.json", "date", True)

            if next_dt:
                from_date = next_dt.date() if isinstance(next_dt, datetime) else next_dt
                print(f"📌 Streszczam {ticker} od {from_date}")
            else:
                from_date = self.start_time.date() if isinstance(self.start_time, datetime) else self.start_time
                print(f"🆕 Streszczam wszystko dla {ticker}")

            # Konwersja do string 'YYYY-MM-DD' dla process_news_range
            from_date_str = from_date.strftime("%Y-%m-%d") if isinstance(from_date, (datetime, date)) else str(
                from_date)
            to_date_str = self.end_time.strftime("%Y-%m-%d")  # końcowa data = dzisiaj

            # Wywołanie funkcji z przekazanymi stringami
            process_news_range(
                start_date=from_date_str,
                end_date=to_date_str,
                TICKER=ticker,
            )

            print(f"✅ Company news summarize dla {ticker} zapisane")

    def fetch_company_news_importance(self):
        scorer = NewsImportanceScorer(batch_size=40)

        for ticker in self.tickers:

            base_path = Path("data") / "company_news_scored"
            next_dt = get_latest_datetime(base_path, ticker, "scored_*.json", "date", True)

            if next_dt:
                from_date = next_dt.date() if isinstance(next_dt, datetime) else next_dt
                print(f"📌 Scoring importance dla {ticker} od {from_date}")
            else:
                from_date = self.start_time.date() if isinstance(self.start_time, datetime) else self.start_time
                print(f"🆕 Scoring wszystkiego dla {ticker}")

            from_date_str = from_date.strftime("%Y-%m-%d") if isinstance(from_date, (datetime, date)) else str(
                from_date)
            to_date_str = self.end_time.strftime("%Y-%m-%d")

            process_importance_range(
                start_date=from_date_str,
                end_date=to_date_str,
                ticker=ticker,
                scorer=scorer
            )

            print(f"✅ Importance scoring dla {ticker} zapisany")

    # Rozszerzona wersja Twojej metody
    def fetch_company_news_summary_with_score(self):
        # Zmieniono na katalog z danymi ocenionymi (scored)
        DATA_DIR = Path("data/company_news_scored")

        for ticker in self.tickers:
            ticker_dir = DATA_DIR / ticker

            # Szukamy plików news_scored.json (lub wzorca, jeśli masz ich więcej)
            for file in ticker_dir.glob("*.json"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for entry in data:
                    # Parsowanie daty
                    news_date = datetime.strptime(
                        entry["date"],
                        "%Y-%m-%d"
                    ).date()

                    # Wscored newsach 'daily_summary' to zazwyczaj string,
                    # ale robimy zabezpieczenie na wypadek listy
                    summary_raw = entry.get("daily_summary", "")
                    summary = " ".join(summary_raw) if isinstance(summary_raw, list) else summary_raw

                    # Pobieramy oceny (default 0.0)
                    importance = float(entry.get("importance", 0.0))

                    # Zapisujemy do bazy przez serwis
                    self.company_daily_summary_service.save(
                        ticker=ticker,
                        date=news_date,
                        summary=summary,
                        importance=importance,
                    )

            print(f"✅ Przetworzono i zapisano scored news dla: {ticker}")

    # Rozszerzona wersja Twojej metody
    def fetch_analyst_grades(self):

        for ticker in self.tickers:
            grades = fetch_analyst_grades(
                symbol=ticker,
                start_date=self.start_time,
                end_date=self.end_time,
            )

            for g in grades:
                as_of_date = datetime.fromisoformat(g["date"]).replace(tzinfo=timezone.utc)

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

            has_start, has_end = self.market_data_service.check_data_coverage(
                ticker=ticker,
                start=self.zero_time,
                end=self.end_time
            )

            if not has_start and not has_end:
                # 🔴 brak wszystkiego → pobierz całość
                fetch_start = self.zero_time
                fetch_end = self.end_time

            else:
                db_start, db_end = self.market_data_service.get_data_range(ticker)

                if has_start and has_end:
                    print(f"✅ Dane dla {ticker} kompletne")
                    continue

                elif has_start and not has_end:
                    # 🟡 brakuje końca
                    fetch_start = db_end + timedelta(days=1)
                    fetch_end = self.end_time

                elif not has_start and has_end:
                    # 🟡 brakuje początku
                    fetch_start = self.zero_time
                    fetch_end = db_start - timedelta(days=2)

            # 📥 pobieranie
            df = self.yahoo_client.fetch_history(
                ticker, fetch_start, fetch_end, interval
            )

            print(f"pobieram od {fetch_start} to {fetch_end}")

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

            print(f"📥 Uzupełniono dane dla {ticker}: {fetch_start} → {fetch_end}")


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
            self.users[user.id] = UserSimulator(
                user_id=user.id,
                starting_cash=cash,
                shares=shares,
                decision_maker=USERS[user.name],
                portfolio_service=self.portfolio_service,
                market_data_service=self.market_data_service,
                valuation_service=self.valuation_service,
                transaction_service=self.transaction_service,
                fundamental_service=self.fundamental_snapshot_service,
                analyst_service=self.analyst_grades_service,
                company_daily_summary_service=self.company_daily_summary_service

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
        while current_time <= self.end_time:
            # Sprawdzamy warunek daty i konkretnej godziny
            if current_time.date() > date(2025, 11, 1):
                if current_time.hour == 13 and current_time.minute == 30:
                    current_time += timedelta(hours=1)

            print(f"Symulacja dla: {current_time}")
            self._simulate_time_step(current_time)

            # Przejście do kolejnego tygodnia
            current_time += timedelta(weeks=1)

        print("✅ Symulacja zakończona.")

    # ---- Krok 4: Symulacja pojedynczego kroku czasu ----
    def _simulate_time_step(self, current_time: datetime):

        # 1️⃣ bierzemy jednego usera tylko do wygenerowania danych
        first_user = next(iter(self.users.values()))

        crucial_indicators = first_user.fetch_or_load_indicators(current_time)

        if not crucial_indicators:
            return

        # 2️⃣ CROSS SECTION – tylko raz
        cross_section_result = first_user.perform_cross_section_once(
            current_time,
            crucial_indicators
        )

        if not cross_section_result:
            return

        # 3️⃣ każdy user podejmuje własną decyzję
        for user_simulator in self.users.values():
            user_simulator.process_day(
                current_time,
                crucial_indicators,
                cross_section_result
            )



